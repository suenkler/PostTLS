import subprocess
import re

from django.shortcuts import render
from django.utils import timezone

from core.models import TLSNotification, TLSLogEntry


def mailaction(request):
    """
    This view is called by the sender of an email that was deferred by Postfix
    because of missing TLS support of the recipients mail server.
    It redirects or deletes the email.
    The view expects URL parameters:
    # /?id=06DA1A40B9B&action=redirect
    or
    # /?id=06DA1A40B9B&action=delete
    """

    ######################################################
    # Get parameters from url
    try:
        queue_id = request.GET.get('queue_id', '')
        action = request.GET.get('action', '')
    except:
        queue_id = ""
        action = ""

    # Show the frontpage if no parameters are given in URL
    if queue_id == "" or action == "":
        return render(request,
                      'core/frontpage.html',
                      {"reason": "no parameters"})

    ######################################################
    # Raise an error if the mail with the given queue id is not
    # existent in the queue on the postfix server
    p = subprocess.Popen(['sudo', 'postcat', '-qh', queue_id],
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    output = str(p.stdout.read(), "utf-8")

    if "No such file or directory" in output:
        return render(request,
                      'core/error.html',
                      {"queue_id": queue_id,
                       "output": output, })

    ######################################################
    # SEND MAIL UNENCRYPTED
    if action == "redirect":

        ##########################################################################
        # Put mail in hold queue so that Postfix does not start another
        # attempt to deliver it.
        p = subprocess.Popen(['sudo', 'postsuper', '-h', queue_id],
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        output = str(p.stdout.read(), "utf-8")

        ##########################################################################
        # Get envelope information
        # We need:
        # - the sender: see below, if we do not pass the sender to sendmail, it sets
        #               "root@mail.domain.com" as the envelope sender. This is
        #               not what we want.
        # - the recipients: we do want to send the mail not to all recipients mentioned
        #                   in the header. The mail was already sent to most of the
        #                   recipients. We just want so send the mail to those recipients
        #                   who did not already get the email since there were errors so
        #                   the mail was not delivered. These are the recipient lines in
        #                   the envelope!

        # Get the envelope for queue_id and grep the line with "recipient:" and "sender:"
        # TODO: Use Python, not egrep!
        p1 = subprocess.Popen(['sudo', 'postcat', '-qe', queue_id], stdout=subprocess.PIPE)
        p2 = subprocess.Popen(['egrep', '^recipient:|sender:'], stdin=p1.stdout, stdout=subprocess.PIPE)
        p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
        envelope = p2.communicate()[0]

        # extract recipient and sender addresses
        recipients = ""
        for line in envelope.decode("utf-8").split('\n'):
            if line is not "":  # there is an empty line at the end after splitting, so make sure it is ignored
                if "recipient:" in line:
                    recipients += re.search('recipient:.(.*)', line).group(1) + " "
                elif "sender:" in line:
                    envelope_sender = re.search('sender:.(.*)', line).group(1)

        ##########################################################################
        # redirect mail to second mail server instance
        #
        # Information about the used sendmail options:
        #
        # -t option extracts recipients from message header. This is *not* what we want!
        #    The mail is already sent to recipients with no errors. We just want to send
        #    the mail to the recipients that had errors. These are mentioned in the
        #    "recipient" lines of the envelope. So we collected them in the variable
        #    "recipients" and pass them to sendmail.
        #
        # -C send mail to specified postfix instance (second postfix instance with opp. TLS)
        #
        # -f option sets the envelope sender.
        #
        # If we do not set the envelope sender, we get this:
        #
        # Received: from [XXX.XXX.XXX.XXX] (helo=mail.domain.com)
        #   by mail2.domain.com with esmtp (Exim 4.84)
        #   (envelope-from <root@mail.domain.com>)
        #   id 1a9pFz-0006zY-0r
        #   for user@domain.com; Fri, 18 Dec 2015 08:15:15 +0100
        #
        # but we want to have this:
        #
        # Received: from [XXX.XXX.XXX.XXX] (helo=mail.domain.com)
        #   by mail2.domain.com with esmtp (Exim 4.84)
        #   (envelope-from <mailbox@suenkler.info>)
        #   id 1a9pD5-00014n-PX
        #   for user@domain.com; Fri, 18 Dec 2015 08:12:16 +0100
        #
        # TODO: Make sure, the sendmail command is correct!
        #       Depending on the environment it could be necessary to set -F (sender full name)
        #       to an empty string.
        p1 = subprocess.Popen(['sudo', 'postcat', '-qbh', queue_id],
                              stdout=subprocess.PIPE)
        p2 = subprocess.Popen(['sendmail', '-C', '/etc/postfix-out/', '-f', envelope_sender, recipients],
                              stdin=p1.stdout,
                              stdout=subprocess.PIPE)
        p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
        output = p2.communicate()[0].decode("utf-8")

        ##########################################################################
        # now delete mail from queue
        p = subprocess.Popen(['sudo', 'postsuper', '-d', queue_id],
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        output += str(p.stdout.read(), "utf-8")

        # Create log entry in database
        q = TLSLogEntry(queue_id=queue_id,
                        sender=envelope_sender,
                        action=action,
                        recipients=recipients,
                        date=timezone.now())
        q.save()

    ######################################################
    # DELETE MAIL
    elif action == "delete":
        ##########################################################################
        # Delete mail from queue
        p = subprocess.Popen(['sudo', 'postsuper', '-d', queue_id],
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        output = str(p.stdout.read(), "utf-8")

    ################################################################################
    # The mail is now deleted or redirected, so we can delete the database entry
    # of the last notification
    try:
        notification = TLSNotification.objects.get(queue_id=queue_id)
    except:
        notification = ""

    if notification:
        notification.delete()

    #######################################################
    # Return Success Page
    return render(request,
                  'core/mailaction.html',
                  {"queue_id": queue_id,
                   "action": action,
                   "output": output, })
