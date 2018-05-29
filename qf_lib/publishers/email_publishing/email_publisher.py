import io
import logging

import emails
import os.path as path
from emails.template import JinjaTemplate as T

from qf_lib.get_sources_root import get_src_root
from qf_lib.settings import Settings


class EmailPublisher(object):
    def __init__(self, settings: Settings):
        self.smtp_settings = settings.smtp
        self.templates_path = path.join(get_src_root(), settings.email_templates_directory)
        self.logger = logging.getLogger(self.__class__.__name__)

    def publish(self, mail_to, subject, template_path, cc=None, bcc=None,
                attachments=(), context=None, templates_encoding='utf8'):
        """
        Creates and sends an e-mail from given templates. It's possible to add some attachments to the message.
        Subject, e-mail addresses (to, cc, bcc) and message template may contain so called "placeholders" like
        {{ username }} (they need to be placed in the double curly brackets). Later it's necessary to pass the context
        parameter from which data will be taken to substitute placeholders

        Parameters
        ----------
        mail_to: str/List[str]
            single e-mail address or the list/tuple of them. It denotes the primary recipients of an e-mail
        subject: str
            subject of the message
        template_path: str
            path (relative to the email_templates_directory set in the settings file) to the template from which
            e-mail should be created
        cc: str/List[str], optional
            the e-mail address (or list of them) of all the CC recipients
        bcc: str/List[str], optional
            the e-mail address (or list of them) of all the CC recipients
        attachments: List[str], optional
            a list of paths to the files which should be attached to an e-mail
        context: dict(str, object), optional
            dictionary with keys of type string. Keys' names should correspond to the names of placeholders
            in the template
        templates_encoding: str, optional
            the encoding of the template. The default one is UTF-8
        """
        self.logger.info("Sending email: '{subject:s}'".format(subject=subject))

        try:
            message = self._create_email(
                mail_to, subject, template_path, cc, bcc, templates_encoding, attachments, context
            )
            self._send_email(message)
            self._log_sent_messages(attachments, bcc, cc, mail_to)
        except Exception as e:
            self.logger.exception("Failed to send emails!")
            raise e

    def _create_email(self, mail_to, subject, template_path, cc, bcc, templates_encoding, attachments, context):
        message = self._create_message_from_template(mail_to, subject, template_path, cc, bcc, templates_encoding)
        message.render(**context)
        self._add_attachments(attachments, message)
        return message

    def _send_email(self, message):
        smtp_settings_dict = {
            'host': self.smtp_settings.host,
            'port': self.smtp_settings.port,
            'tls': self.smtp_settings.tls,
            'user': self.smtp_settings.username,
            'password': self.smtp_settings.password,
            'fail_silently': False
        }
        message.send(smtp=smtp_settings_dict)

    def _create_message_from_template(self, mail_to, subject, template_path, cc, bcc, templates_encoding):
        mail_from = self.smtp_settings.sender

        full_template_path = path.join(self.templates_path, template_path)
        with io.open(full_template_path, 'r', encoding=templates_encoding) as file:
            template_content = file.read()
            file.close()

        message = emails.Message(mail_from=mail_from, mail_to=mail_to, cc=cc, bcc=bcc, subject=T(subject),
                                 html=T(template_content))
        return message

    def _add_attachments(self, attachments, message):
        for file_path in attachments:
            with io.open(file_path, mode='rb') as file:
                filename = path.basename(file_path)
                message.attach(data=file.read(), filename=filename)

    def _log_sent_messages(self, attachments, bcc, cc, mail_to):
        log_info_strings = []
        if attachments:
            log_info_strings.append("Files sent:")
            for attachment in attachments:
                log_info_strings.append("--> {}".format(attachment))
        if mail_to:
            log_info_strings.append("Mail receipents: ")
            for receipent in list(mail_to):
                log_info_strings.append("--> {}".format(receipent))
        if cc:
            log_info_strings.append("CC recepients: ")
            for receipent in list(cc):
                log_info_strings.append("--> {}".format(receipent))
        if bcc:
            log_info_strings.append("BCC recepients: ")
            for receipent in list(bcc):
                log_info_strings.append("--> {}".format(receipent))

        self.logger.info("\n".join(log_info_strings))
