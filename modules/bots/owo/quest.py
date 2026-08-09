import re
import random
import asyncio
import time
import datetime

import discord

from modules.bots.owo.daily import Daily
from modules.utils.component import Component


class Quest:
    SINGLE_PATTERNS = [
        r"Say 'owo' [0-9]+ times!",
        r"[0-9]+ xp from hunting and battling!",
        r"Manually hunt [0-9]+ times!",
        r"Hunt [0-9]+ [a-zA-Z]+ rank animals!",
        r"Battle [0-9]+ times!",
        r"Gamble [0-9]+ times!",
        r"Use an action command on someone [0-9]+ times!",
    ]

    MULTI_PATTERNS = [ 
        r"Battle with a friend [0-9]+ times!",
        r"Receive a cookie from [0-9]+ friends!",
        r"Have a friend pray to you [0-9]+ times!",
        r"Have a friend curse you [0-9]+ times!",
        r"Have a friend use an action command on you [0-9]+ times!",
    ]

    @staticmethod
    def is_single_quest(quest_text):
        return any(re.search(p, quest_text) for p in Quest.SINGLE_PATTERNS)

    @staticmethod
    def is_multi_quest(quest_text):
        return any(re.search(p, quest_text) for p in Quest.MULTI_PATTERNS)

    @staticmethod
    def quest_progress(client, message):
        if not client.doing_quest:
            return
        if not client.is_owo_message(message):
            return
        if not client.current_quest:
            return

        text_complete = f'🎉 | {client.user.mention}, Quest complete:' in message.content

        component_complete = False
        for child in Component.descendants(message):
            content = Component.text(child)
            if f'🎉 **|** {client.user.mention}, You completed a quest:' in content:
                component_complete = True
                break

        if not (text_complete or component_complete):
            return

        client.logger.info(f'Finished quest: {client.current_quest}')
        client.reset_quest_state()

    @staticmethod
    def _has_quest_log_header(message, user):
        for child in Component.descendants(message):
            content = Component.text(child)
            if content and user in content:
                return True
        return False

    @staticmethod
    async def _claim_quest(client, message):
        for button in Component.buttons(message):
            if button.custom_id == 'quests:claim' and not button.disabled:
                try:
                    await button.click()
                except discord.HTTPException:
                    client.logger.exception('Failed to claim quest')
                    return False
                client.logger.info('Claimed quest')
                return True
        return False

    @staticmethod
    def _extract_quests(client, message):
        quests = []
        for child in Component.descendants(message):
            content = Component.text(child)
            if not content:
                continue
            tasks = re.findall(r'\n> (.*?)\n>', content)
            if tasks:
                quest = tasks[0].strip()
                if re.search(r"Defeat [0-9]+ boss(es)?!", quest):
                    client.logger.warning('Detect and skip boss quest')
                    if not client.config['boss']:
                        client.logger.warning('Enable boss mode')
                        client.config['boss'] = True
                    continue
                if not (Quest.is_single_quest(quest) or Quest.is_multi_quest(quest)):
                    client.logger.warning(f'Unknown quest: {quest}')
                    continue
                quests.append(quest)
        return quests

    @staticmethod
    async def do_quest(client):
        if not client.can_run() or not client.config['quest']:
            return
        if client.doing_quest:
            return
        if time.time() < client.cooldown_quest:
            return

        channel = client.current_channel
        if not channel:
            return

        await channel.send(f'{client.prefix}q')
        client.logger.info(f'Sent {client.prefix}q')

        try:
            msg = await client.wait_for(
                'message',
                check=lambda m: (
                    client.is_owo_message(m, in_channel=True)
                    and m.components
                    and Quest._has_quest_log_header(m, client.user.mention)
                ),
                timeout=10,
            )

            if await Quest._claim_quest(client, msg):
                await asyncio.sleep(2)
                msg = await channel.fetch_message(msg.id)

            quests = Quest._extract_quests(client, msg)
            if not quests:
                wait = Daily.reset_time(client.cooldown_reset)
                client.cooldown_quest = wait + time.time()
                client.logger.info(f'All quests done (next in {datetime.timedelta(seconds=wait)})')
                return

            if len(client.clients) == 1:
                selected = None
                for q in quests:
                    if Quest.is_single_quest(q):
                        selected = q
                        break
                if not selected:
                    wait = Daily.reset_time(client.cooldown_reset)
                    client.cooldown_quest = wait + time.time()
                    client.logger.warning('No solo quest available (need multi-account)')
                    return
            else:
                selected = quests[0]

            client.current_quest = selected
            client.doing_quest = True
            client.logger.info(f'Quest: {selected}')

            Quest.set_quest_flag(client, selected)

        except asyncio.TimeoutError:
            client.logger.error('Quest fetch timeout')
        except Exception:
            client.logger.exception('Quest fetch error')

    @staticmethod
    def set_quest_flag(client, q):
        if re.search(r"Say 'owo' [0-9]+ times!", q):
            client.quest_flags['owo'] = True
            client.quest_flags['hunt'] = True
            client.quest_flags['battle'] = True
        elif re.search(r"Earn [0-9]+ xp from hunting and battling!", q):
            client.quest_flags['hunt'] = True
            client.quest_flags['battle'] = True
            client.quest_flags['owo'] = True
        elif re.search(r"Hunt [0-9]+ [a-zA-Z]+ rank animals!|Manually hunt [0-9]+ times!", q):
            client.quest_flags['hunt'] = True
            client.quest_flags['owo'] = True
            client.quest_flags['battle'] = True
        elif re.search(r"Battle [0-9]+ times!", q):
            client.quest_flags['battle'] = True
            client.quest_flags['owo'] = True
            client.quest_flags['hunt'] = True
        elif re.search(r"Gamble [0-9]+ times!", q):
            client.quest_flags['gamble'] = True
        elif re.search(r"Use an action command on someone [0-9]+ times!", q):
            client.quest_flags['action_someone'] = True
            Quest._spawn(client, Quest._do_action_someone(client), 'owo-quest-action-someone')
        elif re.search(r"Battle with a friend [0-9]+ times!", q):
            client.quest_flags['battle_friend'] = True
            Quest._spawn(client, Quest._do_battle_friend(client), 'owo-quest-battle-friend')
        elif re.search(r"Receive a cookie from [0-9]+ friends!", q):
            client.quest_flags['cookie'] = True
            Quest._spawn(client, Quest._do_cookie(client), 'owo-quest-cookie')
        elif re.search(r"Have a friend pray to you [0-9]+ times!", q):
            client.quest_flags['pray'] = True
            Quest._spawn(client, Quest._do_pray(client), 'owo-quest-pray')
        elif re.search(r"Have a friend curse you [0-9]+ times!", q):
            client.quest_flags['curse'] = True
            Quest._spawn(client, Quest._do_curse(client), 'owo-quest-curse')
        elif re.search(r"Have a friend use an action command on you [0-9]+ times!", q):
            client.quest_flags['action_you'] = True
            Quest._spawn(client, Quest._do_action_you(client), 'owo-quest-action-you')

    @staticmethod
    def _spawn(client, coro, name):
        if client.task_manager:
            return client.task_manager.create_background(coro, name=name)
        return asyncio.create_task(coro, name=name)

    @staticmethod
    async def _do_action_someone(client):
        while client.quest_flags.get('action_someone') and client.can_run():
            if client.current_channel:
                action = random.choice(client.owo_actions)
                await client.current_channel.send(f'{client.prefix}{action} {client.owo_bot.mention}')
                client.logger.info(f'Sent {client.prefix}{action} {client.owo_bot.mention}')
            await asyncio.sleep(random.uniform(3, 5))
            if not client.quest_flags.get('action_someone'):
                break
            await asyncio.sleep(5)

    @staticmethod
    async def _do_battle_friend(client):
        while client.quest_flags.get('battle_friend') and client.can_run():
            for other in client.clients:
                if other.user.id == client.user.id or not other.can_run():
                    continue
                other.block_battle = True
                ch = other.current_channel
                if ch:
                    await ch.send(f'{client.prefix}owob {client.user.mention}')
                    other.logger.info(f'Sent {client.prefix}owob {client.user.mention}')
                await asyncio.sleep(random.uniform(3, 5))
                if not client.quest_flags.get('battle_friend'):
                    break
            await asyncio.sleep(15)
        for other in client.clients:
            other.block_battle = False

    @staticmethod
    async def _do_cookie(client):
        while client.quest_flags.get('cookie') and client.can_run():
            for other in client.clients:
                if other.user.id == client.user.id or not other.can_run():
                    continue
                ch = other.current_channel
                if ch:
                    await ch.send(f'owocookie {client.user.id}')
                    other.logger.info(f'Sent owocookie {client.user.id}')
                await asyncio.sleep(random.uniform(3, 5))
                if not client.quest_flags.get('cookie'):
                    break
            wait = Daily.reset_time(client.cooldown_reset)
            client.logger.info(f'Cookie: waiting {datetime.timedelta(seconds=wait)}')
            await asyncio.sleep(wait)

    @staticmethod
    async def _do_pray(client):
        while client.quest_flags.get('pray') and client.can_run():
            for other in client.clients:
                if other.user.id == client.user.id or not other.can_run():
                    continue
                ch = other.current_channel
                if ch:
                    await ch.send(f'owopray {client.user.id}')
                    other.logger.info(f'Sent owopray {client.user.id}')
                await asyncio.sleep(random.uniform(3, 5))
                if not client.quest_flags.get('pray'):
                    break
            await asyncio.sleep(300)

    @staticmethod
    async def _do_curse(client):
        while client.quest_flags.get('curse') and client.can_run():
            for other in client.clients:
                if other.user.id == client.user.id or not other.can_run():
                    continue
                ch = other.current_channel
                if ch:
                    await ch.send(f'owocurse {client.user.id}')
                    other.logger.info(f'Sent owocurse {client.user.id}')
                await asyncio.sleep(random.uniform(3, 5))
                if not client.quest_flags.get('curse'):
                    break
            await asyncio.sleep(300)

    @staticmethod
    async def _do_action_you(client):
        while client.quest_flags.get('action_you') and client.can_run():
            for other in client.clients:
                if other.user.id == client.user.id or not other.can_run():
                    continue
                action = random.choice(client.owo_actions)
                ch = other.current_channel
                if ch:
                    await ch.send(f'{client.prefix}{action} {client.user.mention}')
                    other.logger.info(f'Sent {client.prefix}{action} {client.user.mention}')
                await asyncio.sleep(random.uniform(3, 5))
                if not client.quest_flags.get('action_you'):
                    break
            await asyncio.sleep(5)
