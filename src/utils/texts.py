class BotTexts:
    @staticmethod
    def start_message(name: str):
        return (
            f"""<b>Привет, {name}! 👋</b>

Ищешь надежный и быстрый Proxy? Ты по адресу! 🛡️

🎁 Новым пользователям дарим <b>15 дней</b>!!!

<b>Доступен на всех платформах:</b>
iOS & Android 📱
Windows | macOS | Linux 💻
"""
        )
    
    @staticmethod
    def ref_notif():
        return (
            f"""
💵 Вам начислено <b>30 ₽</b> за приглашение друга!
"""
        )