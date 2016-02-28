from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone

import subprocess
import re
import sys
import datetime
from email.header import decode_header

from core.models import TLSNotification, MandatoryTLSDomains


def send_mail(message, deleted):
    """
    Send mail notification to sender.
    If the domain of a recipient is listed in MandatoryTLSDomains,
    the mail was deleted and 'deleted' is set to True.
    """
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    # Set sender and recipient. Used for header and sendmail function at the end!
    sender = settings.POSTTLS_NOTIFICATION_SENDER
    recipient = message['sender']

    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Alert! Email couldn't be delivered securely!"
    msg['From'] = sender
    msg['To'] = recipient

    # Render mail template
    html_content = render_to_string('core/mail_template.html',
                                    {'recipients': message["recipients"],
                                     'date': message['date'],
                                     'subject': message['subject'],
                                     'queue_id': message['queue_id'],
                                     'postfix_sysadmin_mail_address': settings.POSTTLS_NOTIFICATION_SYSADMIN_MAIL_ADDRESS,
                                     'postfix_tls_host': settings.POSTTLS_TLS_HOST,
                                     'deleted': deleted})

    text_content = strip_tags(html_content)  # this strips the html tags

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text_content, 'plain')
    part2 = MIMEText(html_content, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    # Send the message
    s = smtplib.SMTP(settings.POSTTLS_NOTIFICATION_SMTP_HOST)
    # The sendmail function takes 3 arguments: sender's address,
    # recipient's address and message to send.
    s.sendmail(sender, recipient, msg.as_string())
    s.quit()


class Command(BaseCommand):
    """
    This Custom Management Command processes the Postfix Queue,
    extracts the necessary information and sends email
    notifications to the senders of the queued emails.
    """
    help = 'Process the Postfix queue and send out email notifications'

    def handle(self, *args, **options):

        # parse mailq output to array with one row per message ####
        messages = []
        qline = ["", "", "", "", ""]

        ####################################################
        # Process Mail Queue and get relevant data
        p = subprocess.Popen(['sudo', 'mailq'],
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        output = str(p.stdout.read(), "utf-8").splitlines()

        # Exit if mail queue empty
        if "Mail queue is empty" in " ".join(output):
            sys.exit("Mail queue is empty")

        # If Postfix is trying to deliver mails, exit
        # (the reason for queueing is noted in ())
        if ")" not in " ".join(output):
            sys.exit("Postfix is trying to deliver mails, aborting.")

        # Process mailq output
        for line in output:

            if re.match('^-', line):
                # discard in-queue wrapper
                continue
            elif re.match('^[A-Z0-9]', line):  # queue_id, date and sender
                qline[0] = line.split(" ")[0]  # queue_id
                qline[1] = re.search('^\w*\s*\d*\s(.*\d{2}:\d{2}:\d{2})\s.*@.*$',
                                     line).group(1)  # date
                qline[2] = line[line.rindex(" "):].strip()  # sender
            elif line.count(')') > 0:  # status/reason for deferring
                qline[3] = qline[3] + " " + line.strip()  # merge reasons to one string.
            elif re.match('^\s', line):  # recipient/s
                qline[4] = (qline[4] + " " + line.lstrip()).strip()
            elif not line:  # empty line to recognise the end of a record
                messages.append({"queue_id": qline[0],
                                 "date": qline[1],
                                 "sender": qline[2],
                                 "reasons": qline[3],
                                 "recipients": qline[4]})
                qline = ["", "", "", "", ""]
            else:
                print("  ERROR: unknown input: \"" + line + "\"")

        ####################################################
        # Send email notifications

        for message in messages:

            # Send notification if
            # - queue reason matches the setting and
            # - sender is an internal user
            #
            # Explanation of the second rule:
            # I'm not sure if incoming messages would also be queued here
            # if the next internal hop does not offer TLS. So by checking
            # the sender I make sure that I do not send notifications
            # to external senders of incoming mail.
            if "TLS is required, but was not offered" in message["reasons"] \
                    and "@suenkler.info" in message["sender"]:

                ###################################################################
                # Get subject of mail
                # TODO: Use Python, not grep!
                p1 = subprocess.Popen(['sudo', 'postcat', '-qh', message['queue_id']],
                                      stdout=subprocess.PIPE)
                p2 = subprocess.Popen(['grep', '^Subject: '],
                                      stdin=p1.stdout,
                                      stdout=subprocess.PIPE)
                p1.stdout.close()

                # Subjects are encoded like this:
                # Subject: =?UTF-8?Q?Ein_Betreff_mit_=C3=9Cmlaut?=

                # So, let's decode it:
                subjectlist = decode_header(p2.communicate()[0].decode("utf-8"))

                # decode_header results in a list like this:
                # >>> decode_header('Subject: =?UTF-8?Q?Ein_Betreff_mit_=C3=9Cmlaut?=')
                # [(b'Subject: ', None), (b'Ein Betreff mit \xc3\x9cmlaut', 'utf-8')]

                # Now let's construct the subject line:
                subject = ""
                # Subjects with 'Umlauts' consist of multiple list items:
                if len(subjectlist) > 1:
                    # Iterate over the list, so it doesn't matter if there are email clients out there
                    # that do not encode the whole subject line but, e.g. different parts which
                    # would result in a list with more items than two.
                    for item in subjectlist:
                        # the first list item is
                        if item[1] is None:
                            subject += item[0].decode('utf-8')
                        else:
                            subject += item[0].decode(item[1])
                # If there is just one list item, we have a plain text, not encoded, subject
                # >>> decode_header('Subject: Plain Text')
                # [('Subject: Plain Text', None)]
                else:
                    subject += str(subjectlist[0][0])

                # Remove the string 'Subject: '
                subject = subject.replace("Subject: ", "")

                # set the subject
                message['subject'] = str(subject)

                ###################################################################
                # If the domain is listed in MandatoryTLSDomains, delete the mail and inform the sender
                mandatory_tls = False
                mandatory_tls_domains = MandatoryTLSDomains.objects.all()
                for domain in mandatory_tls_domains:
                    if domain.domain in message["recipients"]:
                        mandatory_tls = True

                if mandatory_tls:
                    # delete mail
                    p = subprocess.Popen(['sudo', 'postsuper', '-d', message['queue_id']],
                                         stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.STDOUT)
                    output = str(p.stdout.read(), "utf-8").splitlines()

                    # send notification to sender
                    send_mail(message, deleted=True)

                else:  # if not mandatory_tls
                    #######################################################################
                    # Send notification and handle database entry

                    # Check the database if an earlier notification was already sent
                    try:
                        notification = TLSNotification.objects.get(queue_id=message["queue_id"])
                    except:
                        notification = ""

                    if not notification:
                        # If this is the first notification, send it and make a database entry
                        n = TLSNotification(queue_id=message["queue_id"], notification=timezone.now())
                        n.save()
                        send_mail(message, deleted=False)
                    else:
                        # If the last notification is more than 30 minutes ago,
                        # send another notification
                        if notification.notification \
                                < timezone.make_aware(datetime.datetime.now(), timezone.get_default_timezone()) \
                                - datetime.timedelta(minutes=30):
                            notification.delete()
                            n = TLSNotification(queue_id=message["queue_id"], notification=timezone.now())
                            n.save()
                            send_mail(message, deleted=False)
