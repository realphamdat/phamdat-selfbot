"""
Gamble: lottery, slot, coinflip, blackjack.
"""

import asyncio
import re
import random
import time
import datetime

from modules.owo.daily import Daily

class Gamble:
    @staticmethod
    async def check_slot(client, message):
        """Check slot result from message edit."""
        if not client.is_owo_message(message, in_channel=True):
            return
        if str(client.nickname) not in message.content:
            return

        c = message.content
        if 'won nothing' in c:
            client.logger.info(f'Slot lost {client.bet_slot}')
            client.bet_slot *= int(client.config['gamble']['slot']['rate'])
        elif '<:eggplant:417475705719226369> <:eggplant:417475705719226369> <:eggplant:417475705719226369>' in c:
            client.logger.info(f'Slot draw {client.bet_slot}')
        elif '<:heart:417475705899712522> <:heart:417475705899712522> <:heart:417475705899712522>' in c:
            client.logger.info(f'Slot won {client.bet_slot} (x2)')
            client.bet_slot = int(client.config['gamble']['slot']['bet'])
        elif '<:cherry:417475705178161162> <:cherry:417475705178161162> <:cherry:417475705178161162>' in c:
            client.logger.info(f'Slot won {client.bet_slot * 2} (x3)')
            client.bet_slot = int(client.config['gamble']['slot']['bet'])
        elif '<:cowoncy:417475705912426496> <:cowoncy:417475705912426496> <:cowoncy:417475705912426496>' in c:
            client.logger.info(f'Slot won {client.bet_slot * 3} (x4)')
            client.bet_slot = int(client.config['gamble']['slot']['bet'])
        elif '<:o_:417475705899843604> <:w_:417475705920684053> <:o_:417475705899843604>' in c:
            client.logger.info(f'Slot won {client.bet_slot * 9} (x10)')
            client.bet_slot = int(client.config['gamble']['slot']['bet'])

    @staticmethod
    async def check_coinflip(client, message):
        """Check coinflip result from message edit."""
        if not client.is_owo_message(message, in_channel=True):
            return
        if str(client.nickname) not in message.content:
            return

        if 'you lost' in message.content:
            client.logger.info(f'Coinflip lost {client.bet_coinflip}')
            client.bet_coinflip *= int(client.config['gamble']['coinflip']['rate'])
        elif 'you won' in message.content:
            client.logger.info(f'Coinflip won {client.bet_coinflip}')
            client.bet_coinflip = int(client.config['gamble']['coinflip']['bet'])

    @staticmethod
    async def lottery(client):
        """Buy lottery ticket."""
        if not client.selfbot_running:
            return
        cfg = client.config['gamble']['lottery']
        if not cfg['mode']:
            return
        if client.cooldown_lottery - time.time() > 0:
            return
        if not client.current_channel:
            return

        amount = cfg['amount']
        await client.current_channel.send(f'{client.prefix}lottery {amount}')
        client.logger.info(f'Sent {client.prefix}lottery {amount}')

        wait = Daily.reset_time(client.config, client.cooldown_reset)
        client.cooldown_lottery = wait + time.time()
        client.logger.info(f'Lottery reset in {datetime.timedelta(seconds=wait)}')

    @staticmethod
    async def play_slot(client):
        """Play slot machine."""
        if not client.selfbot_running or not client.current_channel:
            return

        max_bet = int(client.config['gamble']['slot']['max'])
        if client.bet_slot >= max_bet:
            client.bet_slot = int(client.config['gamble']['slot']['bet'])

        await client.current_channel.send(f'{client.prefix}s {client.bet_slot}')
        client.logger.info(f'Sent {client.prefix}s {client.bet_slot}')

    @staticmethod
    async def play_coinflip(client):
        """Play coinflip."""
        if not client.selfbot_running or not client.current_channel:
            return

        max_bet = int(client.config['gamble']['coinflip']['max'])
        if client.bet_coinflip >= max_bet:
            client.bet_coinflip = int(client.config['gamble']['coinflip']['bet'])

        side = random.choice(['h', 't'])
        await client.current_channel.send(f'{client.prefix}cf {client.bet_coinflip} {side}')
        client.logger.info(f'Sent {client.prefix}cf {client.bet_coinflip} {side}')

    @staticmethod
    async def play_blackjack(client):
        """Play blackjack with auto hit/stand."""
        if not client.selfbot_running or not client.current_channel:
            return

        max_bet = int(client.config['gamble']['blackjack']['max'])
        if client.bet_blackjack >= max_bet:
            client.bet_blackjack = int(client.config['gamble']['blackjack']['bet'])

        await client.current_channel.send(f'{client.prefix}bj {client.bet_blackjack}')
        client.logger.info(f'Sent {client.prefix}bj {client.bet_blackjack}')

        # Auto-play blackjack
        for _ in range(10):
            await asyncio.sleep(random.uniform(2, 3))
            bj_msg = None
            async for msg in client.current_channel.history(limit=10):
                if (client.is_owo_message(msg)
                        and msg.embeds
                        and str(client.user.name) in str(msg.embeds[0].author.name)
                        and 'play blackjack' in str(msg.embeds[0].author.name)):
                    bj_msg = msg
                    break

            if not bj_msg:
                break

            footer = str(bj_msg.embeds[0].footer.text) if bj_msg.embeds[0].footer else ''

            if 'in progress' in footer or 'resuming previous' in footer:
                points = re.findall(r'\[(.*?)\]', bj_msg.embeds[0].fields[1].name)
                if points:
                    my_points = int(points[0])
                    if my_points <= 17:
                        try:
                            await bj_msg.add_reaction('👊')
                            client.logger.info(f'Blackjack {my_points} pts (Hit)')
                        except Exception:
                            pass
                    else:
                        try:
                            await bj_msg.add_reaction('🛑')
                            client.logger.info(f'Blackjack {my_points} pts (Stand)')
                        except Exception:
                            pass
            elif 'You won' in footer:
                client.logger.info(f'Blackjack won {client.bet_blackjack}')
                client.bet_blackjack = int(client.config['gamble']['blackjack']['bet'])
                break
            elif 'You lost' in footer:
                client.logger.info(f'Blackjack lost {client.bet_blackjack}')
                client.bet_blackjack *= int(client.config['gamble']['blackjack']['rate'])
                break
            elif 'You tied' in footer or 'You both bust' in footer:
                client.logger.info(f'Blackjack draw')
                break
            else:
                break

    @staticmethod
    async def gamble_cycle(client):
        """Run one gamble cycle."""
        cfg = client.config['gamble']
        delay_min = cfg['delay']['min']
        delay_max = cfg['delay']['max']

        try:
            if cfg['lottery']['mode']:
                await Gamble.lottery(client)
                await asyncio.sleep(random.uniform(delay_min, delay_max))

            if cfg['slot']['mode'] or client.quest_flags.get('gamble'):
                await Gamble.play_slot(client)
                await asyncio.sleep(random.uniform(delay_min, delay_max))

            if cfg['coinflip']['mode'] or client.quest_flags.get('gamble'):
                await Gamble.play_coinflip(client)
                await asyncio.sleep(random.uniform(delay_min, delay_max))

            if cfg['blackjack']['mode'] or client.quest_flags.get('gamble'):
                await Gamble.play_blackjack(client)
        except Exception:
            client.logger.exception('Gamble error')