import re
import random
import asyncio
import time
import datetime

from modules.owo.daily import Daily

class Quest:
    SINGLE_PATTERNS = [
        r"Say 'owo' [0-9]+ times!",
        r"[0-9]+ xp from hunting and battling!",
        r"Manually hunt [0-9]+ times!",
        r"Hunt [0-9]+ animals that are (.*?) rank!",
        r"Battle [0-9]+ times!",
        r"Gamble [0-9]+ times!",
        r"Use an action command on someone [0-9]+ times!",
    ]

    @staticmethod
    def is_single_quest(quest_text): return any(re.findall(p, quest_text) for p in Quest.SINGLE_PATTERNS)

    @staticmethod
    async def quest_progress(client, message):
        if not client.doing_quest: return
        if not client.is_owo_message(message): return
        if not client.current_quest: return

        reward = client.current_quest[1] if len(client.current_quest) > 1 else ''
        if f'You finished a quest and earned: {reward}!' not in message.content: return

        client.logger.info(f'Finished quest: {client.current_quest[0]}')
        client.doing_quest = False
        for key in client.quest_flags: client.quest_flags[key] = False
        client.current_quest = None

    @staticmethod
    async def do_quest(client):
        if not client.selfbot_running or not client.config['quest']: return
        if client.doing_quest: return
        if client.cooldown_quest - time.time() > 0: return

        channel = client.current_channel
        if not channel: return

        await channel.send(f'{client.prefix}q')
        client.logger.info(f'Sent {client.prefix}q')

        try:
            msg = await client.wait_for(
                'message',
                check = lambda m: (
                    client.is_owo_message(m, in_channel = True)
                    and m.embeds
                    and m.embeds[0].description
                    and f'These quests belong to <@{client.user.id}>' in m.embeds[0].description
                ),
                timeout = 10,
            )

            desc = msg.embeds[0].description

            if 'You finished all of your quests' in desc:
                wait = Daily.reset_time(client.cooldown_reset)
                client.cooldown_quest = wait + time.time()
                client.logger.info(f'All quests done (next in {datetime.timedelta(seconds=wait)})')
                return

            # Parse quests
            tasks = re.findall(r'\*\*[1-3]. (.*?)\*\*', desc)
            rewards = re.findall(r'<:blank:427371936482328596>`‣ Reward:` (.*?)\n<:blank:427371936482328596>', desc)
            quests = list(zip(tasks, rewards))

            if not quests: return

            if len(client.clients) == 1:
                selected = None
                for q in quests:
                    if Quest.is_single_quest(q[0]):
                        selected = q
                        break
                if not selected:
                    wait = Daily.reset_time(client.cooldown_reset)
                    client.cooldown_quest = wait + time.time()
                    client.logger.warning(f'No solo quest available (need multi-account)')
                    return
            else: selected = quests[0]

            client.current_quest = list(selected)
            client.doing_quest = True
            client.logger.info(f'Quest: {selected[0]} (reward: {selected[1]})')

            q = selected[0]

            if re.findall(r"Say 'owo' [0-9]+ times!", q):
                client.quest_flags['owo'] = True
                client.quest_flags['hunt'] = True
                client.quest_flags['battle'] = True
            elif re.findall(r"[0-9]+ xp from hunting and battling!", q):
                client.quest_flags['hunt'] = True
                client.quest_flags['battle'] = True
                client.quest_flags['owo'] = True
            elif re.findall(r"Hunt [0-9]+ animals|Manually hunt [0-9]+ times", q):
                client.quest_flags['hunt'] = True
                client.quest_flags['owo'] = True
                client.quest_flags['battle'] = True
            elif re.findall(r"Battle [0-9]+ times!", q):
                client.quest_flags['battle'] = True
                client.quest_flags['owo'] = True
                client.quest_flags['hunt'] = True
            elif re.findall(r"Gamble [0-9]+ times!", q):
                client.quest_flags['gamble'] = True
            elif re.findall(r"Use an action command on someone [0-9]+ times!", q):
                client.quest_flags['action_someone'] = True
                Quest._spawn(client, Quest._do_action_someone(client), 'owo-quest-action-someone')
            elif re.findall(r"Battle with a friend [0-9]+ times!", q):
                client.quest_flags['battle_friend'] = True
                Quest._spawn(client, Quest._do_battle_friend(client), 'owo-quest-battle-friend')
            elif re.findall(r"Receive a cookie from [0-9]+ friends!", q):
                client.quest_flags['cookie'] = True
                Quest._spawn(client, Quest._do_cookie(client), 'owo-quest-cookie')
            elif re.findall(r"Have a friend pray to you [0-9]+ times!", q):
                client.quest_flags['pray'] = True
                Quest._spawn(client, Quest._do_pray(client), 'owo-quest-pray')
            elif re.findall(r"Have a friend curse you [0-9]+ times!", q):
                client.quest_flags['curse'] = True
                Quest._spawn(client, Quest._do_curse(client), 'owo-quest-curse')
            elif re.findall(r"Have a friend use an action command on you [0-9]+ times!", q):
                client.quest_flags['action_you'] = True
                Quest._spawn(client, Quest._do_action_you(client), 'owo-quest-action-you')

        except asyncio.TimeoutError: client.logger.error('Quest fetch timeout')
        except Exception: client.logger.exception('Quest fetch error')

    @staticmethod
    def _spawn(client, coro, name):
        if getattr(client, 'task_manager', None):
            return client.task_manager.create_background(coro, name=name)
        return asyncio.create_task(coro, name=name)

    @staticmethod
    async def _do_action_someone(client):
        while client.quest_flags.get('action_someone') and client.selfbot_running:
            if client.current_channel:
                action = random.choice(client.owo_actions)
                await client.current_channel.send(f'{client.prefix}{action} <@{client.owo_bot.id}>')
                client.logger.info(f'Sent {client.prefix}{action}')
            await asyncio.sleep(random.uniform(3, 5))

    @staticmethod
    async def _do_battle_friend(client):
        while client.quest_flags.get('battle_friend') and client.selfbot_running:
            for other in client.clients:
                if other.user.id == client.user.id or not other.selfbot_running: continue
                other.block_battle = True
                try:
                    ch = other.current_channel
                    if ch:
                        await ch.send(f'owob <@{client.user.id}>')
                        other.logger.info(f'Sent owob <@{client.user.id}>')
                except Exception: client.logger.exception('Battle friend error')
                await asyncio.sleep(random.uniform(3, 5))
                if not client.quest_flags.get('battle_friend'): break
            await asyncio.sleep(15)
        for other in client.clients: other.block_battle = False

    @staticmethod
    async def _do_cookie(client):
        while client.quest_flags.get('cookie') and client.selfbot_running:
            for other in client.clients:
                if other.user.id == client.user.id or not other.selfbot_running: continue
                ch = other.current_channel
                if ch:
                    await ch.send(f'owocookie {client.user.id}')
                    other.logger.info(f'Sent owocookie {client.user.id}')
                await asyncio.sleep(random.uniform(3, 5))
                if not client.quest_flags.get('cookie'): break
            wait = Daily.reset_time(client.cooldown_reset)
            client.logger.info(f'Cookie: waiting {datetime.timedelta(seconds=wait)}')
            await asyncio.sleep(wait)

    @staticmethod
    async def _do_pray(client):
        while client.quest_flags.get('pray') and client.selfbot_running:
            for other in client.clients:
                if other.user.id == client.user.id or not other.selfbot_running: continue
                other.block_pray_curse = True
                ch = other.current_channel
                if ch:
                    await ch.send(f'owopray {client.user.id}')
                    other.logger.info(f'Sent owopray {client.user.id}')
                await asyncio.sleep(random.uniform(3, 5))
                if not client.quest_flags.get('pray'): break
            await asyncio.sleep(300)
        for other in client.clients: other.block_pray_curse = False

    @staticmethod
    async def _do_curse(client):
        while client.quest_flags.get('curse') and client.selfbot_running:
            for other in client.clients:
                if other.user.id == client.user.id or not other.selfbot_running: continue
                other.block_pray_curse = True
                ch = other.current_channel
                if ch:
                    await ch.send(f'owocurse {client.user.id}')
                    other.logger.info(f'Sent owocurse {client.user.id}')
                await asyncio.sleep(random.uniform(3, 5))
                if not client.quest_flags.get('curse'): break
            await asyncio.sleep(300)
        for other in client.clients: other.block_pray_curse = False

    @staticmethod
    async def _do_action_you(client):
        while client.quest_flags.get('action_you') and client.selfbot_running:
            for other in client.clients:
                if other.user.id == client.user.id or not other.selfbot_running: continue
                action = random.choice(client.owo_actions)
                ch = other.current_channel
                if ch:
                    await ch.send(f'owo{action} <@{client.user.id}>')
                    other.logger.info(f'Sent owo{action} <@{client.user.id}>')
                await asyncio.sleep(random.uniform(3, 5))
                if not client.quest_flags.get('action_you'): break
            await asyncio.sleep(5)
