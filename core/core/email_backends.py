from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings
from sib_api_v3_sdk import ApiClient, Configuration, TransactionalEmailsApi
from sib_api_v3_sdk.models import SendSmtpEmail

class BrevoBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        configuration = Configuration()
        configuration.api_key['api-key'] = settings.BREVO_API_KEY
        api_instance = TransactionalEmailsApi(ApiClient(configuration))

        sent_count = 0

        for message in email_messages:
            try:
                email = SendSmtpEmail(
                    to=[{"email": message.to[0]}],
                    sender={"email": settings.DEFAULT_FROM_EMAIL.split("<")[-1].replace(">", ""),
                            "name": settings.DEFAULT_FROM_EMAIL.split("<")[0].strip()},
                    subject=message.subject,
                    html_content=message.body
                )
                api_instance.send_transac_email(email)
                sent_count += 1
            except Exception as e:
                if not self.fail_silently:
                    raise e
        return sent_count
