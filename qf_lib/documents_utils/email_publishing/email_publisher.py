#     Copyright 2016-present CERN – European Organization for Nuclear Research
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

import io
import os.path as path
from typing import List, Union, Dict

import emails
from emails.template import JinjaTemplate as T

from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.settings import Settings
from qf_lib.starting_dir import get_starting_dir_abs_path


class EmailPublisher:
    """Used to create and send an e-mail from given templates.
    """
    def __init__(self, settings: Settings):
        self.smtp_settings = settings.smtp
        self.templates_path = path.join(get_starting_dir_abs_path(), settings.email_templates_directory)
        self.logger = qf_logger.getChild(self.__class__.__name__)

    def publish(self, mail_to: Union[str, List[str]], subject: str, template_path: str,
                cc: Union[str, List[str]] = None, bcc: Union[str, List[str]] = None, attachments: List[str] = (),
                context: Dict[str, object] = None, templates_encoding: str = 'utf8'):
        """
        Creates and sends an e-mail from given templates. It's possible to add some attachments to the message.
        Subject, e-mail addresses (to, cc, bcc) and message template may contain so called "placeholders" like
        {{ username }} (they need to be placed in the double curly brackets). Later it's necessary to pass the context
        parameter from which data will be taken to substitute placeholders

        Parameters
        ----------
        mail_to
            single e-mail address or the list/tuple of them. It denotes the primary recipients of an e-mail
        subject
            subject of the message
        template_path
            path (relative to the email_templates_directory set in the settings file) to the template from which
            e-mail should be created
        cc
            the e-mail address (or list of them) of all the CC recipients
        bcc
            the e-mail address (or list of them) of all the CC recipients
        attachments
            a list of paths to the files which should be attached to an e-mail
        context
            dictionary with keys of type string. Keys' names should correspond to the names of placeholders
            in the template
        templates_encoding
            the encoding of the template. The default one is UTF-8
        """
        self.logger.info("Sending email: '{subject:s}'".format(subject=subject))

        try:
            message = self._create_email(
                mail_to, subject, template_path, cc, bcc, templates_encoding, attachments, context)
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

        message = emails.Message(
            mail_from=mail_from, mail_to=mail_to, cc=cc, bcc=bcc, subject=T(subject), html=T(template_content))
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
            mail_to, _ = convert_to_list(mail_to, str)
            for receipent in list(mail_to):
                log_info_strings.append("--> {}".format(receipent))
        if cc:
            log_info_strings.append("CC recepients: ")
            cc, _ = convert_to_list(cc, str)
            for receipent in list(cc):
                log_info_strings.append("--> {}".format(receipent))
        if bcc:
            log_info_strings.append("BCC recepients: ")
            bcc, _ = convert_to_list(bcc, str)
            for receipent in list(bcc):
                log_info_strings.append("--> {}".format(receipent))

        self.logger.info("\n".join(log_info_strings))
