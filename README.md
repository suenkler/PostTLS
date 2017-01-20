PostTLS - Postfix's Transport Encryption under Control of the User
==================================================================

PostTLS is an addition to the excellent Postfix mail server. It allows to activate mandatory TLS for all domains in practice (e.g. to set `smtp_tls_security_level = encrypt`). PostTLS does this by enabling the sender of an email to delete or to send the email unencrypted if a secure connection cannot be established (e.g. because the recipients' mail server does not support transport encryption) and thus the mail was deferred to the Postfix queue. More information can be found at [https://posttls.com](https://posttls.com).

License
-------

The code in this repository is licensed under version 3 of the GNU Affero General Public License (AGPLv3). Please see the LICENSE file for details.

Requirements
------------

Please be aware that PostTLS right now is in **early stage** and there are quite a few things to prepare on the server to use the software. You should be familiar with Linux system administration and you should know how to run a python program in production. In the following you will find a list of requirements - but this is **not a step-by-step guide to meet these requirements**! Of course, documentation and automation of the installation procedure will be enhanced in the future if there is demand. 

**USE THIS SOFTWARE AT YOUR OWN RISK! AND MAKE SURE YOU UNDERSTAND WHAT IT DOES!**

Make sure to meet the following requirements:

- Python 3
- Virtualenv and virtualenvwrapper
- Two Postfix instances. See [Managing multiple Postfix instances on a single host](http://www.postfix.org/MULTI_INSTANCE_README.html) to find out more about multiple instance support of Postfix.
  - First instance: Postfix option `smtp_tls_security_level` is set to `encrypt` and implements mandatory TLS for all domains. 
  - Second instance: Postfix option `smtp_tls_security_level` is set to `may` and implements opportunistic TLS.
- PostTLS calls some Postfix commands, which should be executable via sudo without password. So add something like this to /etc/sudoers using `sudo visudo`:

```bash
# User hendrik can use apps needed for PostTLS
hendrik ALL = NOPASSWD: /usr/bin/mailq
hendrik ALL = NOPASSWD: /usr/sbin/postcat
hendrik ALL = NOPASSWD: /usr/sbin/postsuper
```

Installation
------------

If the above mentioned requirements are met, you should be able to install and use PostTLS.

Create a virtual environment:

    $ mkvirtualenv posttls

Clone the repository:

    $ git clone https://github.com/suenkler/PostTLS.git

Install Python requirements:

    $ pip install -r requirements.txt

Configuration of PostTLS is done via environment variables. You can use a bash script `env.sh` like this:

```bash
# Django configuration
export POSTTLS_SECRET_KEY="verysecretkey"
export POSTTLS_STATIC_ROOT_DIR="/home/hendrik/apps/posttls/static/"
export POSTTLS_MEDIA_ROOT_DIR="/home/hendrik/apps/posttls/media/"

# Set this to 'production' in production environment (see Django settings file)
export POSTTLS_ENVIRONMENT_TYPE="development"

# PostTLS settings
export POSTTLS_NOTIFICATION_SYSADMIN_MAIL_ADDRESS="admin@localhost"
export POSTTLS_NOTIFICATION_SENDER="postmaster@domain.com (Postmaster)"
export POSTTLS_NOTIFICATION_SMTP_HOST="localhost"

# Needed to generate the links in the notification mail:
export POSTTLS_TLS_HOST="server.domain.com"
```

PostTLS uses an SQLite database. But since Django supports a wide range of different databases, you can also choose a full-fledged database such as PostgreSQL. Create database tables:

    $ ./manage.py migrate

Check if the script to query the Postfix queue runs smoothly:

    $ ./manage.py process_queue

In the notification email sent by the Django management command `process_queue` you will find two buttons which link to the web server of our PostTLS installation. Make these features available by configuring a web server. For testing purposes you can use Django's build-in development server by running:

    $ ./manage.py runserver 0.0.0.0:8000

Now you should be able to access PostTLS via your web browser.

Please note, that you should not use Django's development server in production. There are many different technology stacks to run a Django application in production. One option is to use Gunicorn behind Nginx as a reverse proxy.

Automation
----------

You can configure a cron job to process the queue once every minute. To prevent overlapping of cron jobs, use the [flock](http://linux.die.net/man/1/flock) command:

    */1 * * * * . /home/hendrik/apps/posttls/env.sh && /usr/bin/flock -w 0 /home/hendrik/apps/posttls/cron.lock /home/hendrik/.virtualenvs/posttls/bin/python3 /home/hendrik/apps/posttls/posttls/posttls/manage.py process_queue >/dev/null 2>&1
