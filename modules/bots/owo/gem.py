import asyncio
import re
import random
import time
import datetime

GEM_TIERS = {
    'gem1': range(51, 58),
    'gem3': range(65, 72),
    'gem4': range(72, 79),
    'star': range(79, 86),
}


class Gem:
    @staticmethod
    def _skip_gem_check(client):
        if not client.no_gem:
            return False
        if time.time() - client.no_gem_since >= 3600:
            client.no_gem = False
            return False
        return True

    @staticmethod
    def _active_tier_names(client, gem):
        tiers = ['gem1', 'gem3', 'gem4']
        if gem.get('star') and client.special_pet_available:
            tiers.append('star')
        return tiers

    @staticmethod
    async def _send_use(client, gem_str):
        if not gem_str or not client.can_run() or not client.current_channel:
            return
        await client.current_channel.send(f'{client.prefix}use {gem_str}')
        client.logger.info(f'Sent {client.prefix}use {gem_str}')
        client.no_gem = False
        try:
            await client.wait_for(
                'message',
                check=lambda m: (
                    client.is_owo_message(m, in_channel=True)
                    and client.msg_contains(m.content, all_of=[str(client.nickname), 'active Special gem or you do not own'])
                ),
                timeout=5
            )
            client.special_pet_available = False
        except asyncio.TimeoutError:
            pass

    @staticmethod
    async def get_inventory(client):
        await asyncio.sleep(2)
        if not client.can_run() or not client.current_channel:
            return []
        await client.current_channel.send(f'{client.prefix}inv')
        client.logger.info(f'Sent {client.prefix}inv')
        try:
            msg = await client.wait_for(
                'message',
                check=lambda m: (
                    client.is_owo_message(m, in_channel=True)
                    and f"{client.nickname}'s Inventory" in m.content
                ),
                timeout=5,
            )
            client.inventory_str = msg.content
            inv = [int(x) for x in re.findall(r'`(.*?)`', msg.content) if x.isnumeric()]
            
            await Gem._open_items(client, inv)
            return inv
        except asyncio.TimeoutError:
            client.logger.error('Inventory fetch timeout')
            return []

    @staticmethod
    async def _open_items(client, inv):
        opening = client.config['gem']['openning']
        if opening['box'] and 50 in inv:
            if not client.can_run() or not client.current_channel:
                return
            await client.current_channel.send(f'{client.prefix}lb all')
            client.logger.info(f'Sent {client.prefix}lb all')
            await asyncio.sleep(2)
        if opening['crate'] and 100 in inv:
            if not client.can_run() or not client.current_channel:
                return
            await client.current_channel.send(f'{client.prefix}wc all')
            client.logger.info(f'Sent {client.prefix}wc all')
            await asyncio.sleep(2)
        if opening['flootbox'] and 49 in inv:
            if not client.can_run() or not client.current_channel:
                return
            await client.current_channel.send(f'{client.prefix}lb f')
            client.logger.info(f'Sent {client.prefix}lb f')
            await asyncio.sleep(2)

    @staticmethod
    async def _couple_gem(client, gem):
        if Gem._skip_gem_check(client):
            return
        inv = await Gem.get_inventory(client)
        if not inv:
            return

        active = Gem._active_tier_names(client, gem)
        if not active:
            return

        starts = {t: GEM_TIERS[t].start for t in active}
        max_n = min(GEM_TIERS[t].stop - starts[t] for t in active)

        valid = []
        for n in range(max_n):
            combo = [starts[t] + n for t in active]
            if all(c in inv and c in GEM_TIERS[t] for c, t in zip(combo, active)):
                valid.append(combo)

        if not valid:
            client.no_gem = True
            client.no_gem_since = time.time()
            client.logger.info('No couple gems available')
            return

        selected = valid[-1] if gem['best'] else valid[0]
        await Gem._send_use(client, ' '.join(map(str, selected)))

    @staticmethod
    async def _single_gem(client, gem, tiers_to_use=None):
        if Gem._skip_gem_check(client):
            return
        inv = await Gem.get_inventory(client)
        if not inv:
            return

        if tiers_to_use is None:
            tiers_to_use = Gem._active_tier_names(client, gem)

        gems = []
        for tier in tiers_to_use:
            tier_range = GEM_TIERS.get(tier)
            if not tier_range:
                continue
            if tier == 'star' and not (gem.get('star') and client.special_pet_available):
                continue
            available = [g for g in inv if g in tier_range]
            if available:
                gems.append(str(max(available) if gem['best'] else min(available)))

        if gems:
            await Gem._send_use(client, ' '.join(gems))
        else:
            client.no_gem = True
            client.no_gem_since = time.time()
            client.logger.info(f'No {", ".join(tiers_to_use)} gems available')

    @staticmethod
    async def check_gem(client, message):
        if not client.can_run():
            return
        if not client.is_owo_message(message, in_channel=True):
            return
        if not client.msg_contains(message.content, all_of=[str(client.nickname), '🌱', 'gained']):
            return

        gem = client.config['gem']
        if not gem['use']:
            return
        if Gem._skip_gem_check(client):
            return

        if gem['couple'] and 'spent 5 <:cowoncy:416043450337853441> and caught a' in message.content:
            await Gem._couple_gem(client, gem)
        else:
            inv_text = client.inventory_str
            empty = [tier for tier in GEM_TIERS if tier not in message.content and tier in inv_text]
            if empty:
                await Gem._single_gem(client, gem, tiers_to_use=empty)

    @staticmethod
    def glitch_available(client):
        gem = client.config['gem']
        if not gem.get('glitch', False):
            return False
        if time.time() < client.cooldown_glitch:
            return False
        return True

    @staticmethod
    async def check_glitch(client):
        if not Gem.glitch_available(client) or not client.current_channel:
            return
        await client.current_channel.send(f'{client.prefix}dt')
        client.logger.info(f'Sent {client.prefix}dt')
        try:
            msg = await client.wait_for(
                'message',
                check=lambda m: (
                    client.is_owo_message(m, in_channel=True)
                    and client.msg_contains(m.content, any_of=['are available', 'not available'])
                ),
                timeout=5,
            )
            if 'are available' in msg.content:
                parts = re.findall(r'\*\*(.*?)\*\*', msg.content)
                if len(parts) >= 3:
                    nums = re.findall(r'[0-9]+', parts[2])
                    if len(nums) == 1:
                        duration = int(nums[0])
                    elif len(nums) == 2:
                        duration = int(nums[0]) * 60 + int(nums[1])
                    elif len(nums) >= 3:
                        duration = int(nums[0]) * 3600 + int(nums[1]) * 60 + int(nums[2])
                    else:
                        duration = 600
                    client.cooldown_glitch = duration + time.time()
                    client.logger.info(f'Glitch available ({datetime.timedelta(seconds=duration)})')
            elif 'not available' in msg.content:
                client.logger.info('Glitch not available')
        except asyncio.TimeoutError:
            client.logger.error('Glitch check timeout')
