import asyncio
import re
import time
import datetime

class Daily:
    @staticmethod
    def reset_time(cooldown_reset = 0):
        if cooldown_reset != 0: return cooldown_reset

        # reset_cfg = {"hour": 7, "minute": 0, "second": 0, "microsecond": 0}
        now = datetime.datetime.now(datetime.timezone.utc)
        reset = now.replace(hour = 7, minute = 0, second = 0, microsecond = 0)
        if now >= reset: reset += datetime.timedelta(days = 1)

        return int((reset - now).total_seconds()) + 30

    @staticmethod
    async def claim(client):
        if not client.selfbot_running: return
        if client.cooldown_daily - time.time() > 0: return

        channel = client.current_channel
        if not channel: return

        await channel.send(f'{client.prefix}daily')
        client.logger.info(f'Sent {client.prefix}daily')

        try:
            msg = await client.wait_for(
                'message',
                check = lambda m: (
                    client.is_owo_message(m, in_channel = True)
                    and client.msg_contains(m, all_of = [str(client.nickname)])
                    and client.msg_contains(m, any_of = ['next daily', 'Nu'])
                ),
                timeout = 10,
            )

            time_data = re.findall(r'(\d+)H|(\d+)M|(\d+)S', msg.content.split('!')[-1].strip())
            hours = int(time_data[0][0]) if time_data and time_data[0][0] else 0
            minutes = int(time_data[1][1]) if len(time_data) > 1 and time_data[1][1] else 0
            seconds = int(time_data[2][2]) if len(time_data) > 2 and time_data[2][2] else 0
            wait = hours * 3600 + minutes * 60 + seconds

            client.cooldown_reset = wait
            client.cooldown_daily = wait + time.time()

            if 'next daily' in msg.content: client.logger.info(f'Claimed daily (next in {datetime.timedelta(seconds=wait)})')
            elif 'Nu' in msg.content: client.logger.info(f'Daily not ready (wait {datetime.timedelta(seconds=wait)})')

        except asyncio.TimeoutError: client.logger.error('Daily claim timeout')