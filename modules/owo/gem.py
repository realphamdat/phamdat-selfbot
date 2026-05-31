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
        if not getattr(client, 'no_gem', False): return False
        if time.time() - getattr(client, 'no_gem_since', 0) >= 300:
            client.no_gem = False
            return False
        return True

    @staticmethod
    def _active_tier_names(client, cfg):
        tiers = ['gem1', 'gem3', 'gem4']
        if cfg.get('star') and getattr(client, 'special_pet_available', False): tiers.append('star')
        return tiers

    @staticmethod
    async def _send_use(client, gem_str):
        if not gem_str: return
        await client.current_channel.send(f'{client.prefix}use {gem_str}')
        client.logger.info(f'Sent {client.prefix}use {gem_str}')
        client.no_gem = False
        try:
            await client.wait_for(
                'message',
                check = lambda m: (
                    client.is_owo_message(m, in_channel = True)
                    and client.msg_contains(m, all_of = [str(client.nickname), 'active Special gem or you do not own'])
                ),
                timeout = 10
            )
            client.special_pet_available = False
        except asyncio.TimeoutError: pass

    @staticmethod
    async def get_inventory(client):
        await asyncio.sleep(random.uniform(2, 3))
        if not client.current_channel: return []
        await client.current_channel.send(f'{client.prefix}inv')
        client.logger.info(f'Sent {client.prefix}inv')
        try:
            msg = await client.wait_for(
                'message',
                check = lambda m: (
                    client.is_owo_message(m, in_channel = True)
                    and f"{client.nickname}'s Inventory" in m.content
                ),
                timeout = 10,
            )
            client.inventory_str = msg.content
            inv = [int(x) for x in re.findall(r'`(.*?)`', msg.content) if x.isnumeric()]
            await asyncio.sleep(random.uniform(2, 3))
            await Gem._open_items(client, inv)
            return inv
        except asyncio.TimeoutError:
            client.logger.error('Inventory fetch timeout')
            return []

    @staticmethod
    async def _open_items(client, inv):
        cfg = client.config['gem']['openning']
        if cfg['box'] and 50 in inv:
            await client.current_channel.send(f'{client.prefix}lb all')
            client.logger.info(f'Sent {client.prefix}lb all')
            await asyncio.sleep(random.uniform(2, 3))
        if cfg['crate'] and 100 in inv:
            await client.current_channel.send(f'{client.prefix}wc all')
            client.logger.info(f'Sent {client.prefix}wc all')
            await asyncio.sleep(random.uniform(2, 3))
        if cfg['flootbox'] and 49 in inv:
            await client.current_channel.send(f'{client.prefix}lb f')
            client.logger.info(f'Sent {client.prefix}lb f')
            await asyncio.sleep(random.uniform(2, 3))

    @staticmethod
    async def _couple_gem(client, cfg):
        if Gem._skip_gem_check(client): return
        inv = await Gem.get_inventory(client)
        if not inv: return

        active = Gem._active_tier_names(client, cfg)
        if not active: return

        starts = {t: GEM_TIERS[t].start for t in active}
        max_n = min(GEM_TIERS[t].stop - starts[t] for t in active)

        valid = []
        for n in range(max_n):
            combo = [starts[t] + n for t in active]
            if all(c in inv and c in GEM_TIERS[t] for c, t in zip(combo, active)): valid.append(combo)

        if not valid:
            client.no_gem = True
            client.no_gem_since = time.time()
            client.logger.info('No couple gems available, disabling further attempts for 5 min')
            return

        selected = valid[-1] if cfg['best'] else valid[0]
        await Gem._send_use(client, ' '.join(map(str, selected)))

    @staticmethod
    async def _single_gem(client, cfg, tiers_to_use=None):
        if Gem._skip_gem_check(client): return
        inv = await Gem.get_inventory(client)
        if not inv: return

        if tiers_to_use is None: tiers_to_use = Gem._active_tier_names(client, cfg)

        gems = []
        for tier in tiers_to_use:
            tier_range = GEM_TIERS.get(tier)
            if not tier_range: continue
            if tier == 'star' and not (cfg.get('star') and getattr(client, 'special_pet_available', False)): continue
            available = [g for g in inv if g in tier_range]
            if available: gems.append(str(max(available) if cfg['best'] else min(available)))

        if gems: await Gem._send_use(client, ' '.join(gems))
        else:
            client.no_gem = True
            client.no_gem_since = time.time()
            client.logger.info(f'No {tiers_to_use} gems available, disabling further attempts for 5 min')

    @staticmethod
    async def check_gem(client, message):
        if not getattr(client, 'selfbot_running', False): return
        if not client.is_owo_message(message, in_channel = True): return
        if not client.msg_contains(message, all_of = [str(client.nickname), '🌱', 'gained']): return

        cfg = client.config['gem']
        if not cfg['use']: return
        if Gem._skip_gem_check(client): return

        if cfg['couple'] and 'spent 5 <:cowoncy:416043450337853441> and caught a' in message.content:
            await Gem._couple_gem(client, cfg)
        else:
            inv_text = getattr(client, 'inventory_str', '')
            empty = [tier for tier in GEM_TIERS if tier not in message.content and tier in inv_text]
            if empty: await Gem._single_gem(client, cfg, tiers_to_use=empty)

    @staticmethod
    def glitch_available(client):
        cfg = client.config['gem']
        if not cfg.get('glitch', False): return False
        if getattr(client, 'cooldown_glitch', 0) - time.time() > 0: return False
        if not getattr(client, 'glitch_loop_ran', True): return False
        return True

    @staticmethod
    async def check_glitch(client):
        if not Gem.glitch_available(client) or not client.current_channel: return
        await client.current_channel.send(f'{client.prefix}dt')
        client.logger.info(f'Sent {client.prefix}dt')
        try:
            msg = await client.wait_for(
                'message',
                check = lambda m: (
                    client.is_owo_message(m, in_channel = True)
                    and client.msg_contains(m, any_of = ['are available', 'not available'])
                ),
                timeout = 10,
            )
            if 'are available' in msg.content:
                parts = re.findall(r'\*\*(.*?)\*\*', msg.content)
                if len(parts) >= 3:
                    nums = re.findall(r'[0-9]+', parts[2])
                    if len(nums) == 1: wait = int(nums[0])
                    elif len(nums) == 2: wait = int(nums[0]) * 60 + int(nums[1])
                    elif len(nums) >= 3: wait = int(nums[0]) * 3600 + int(nums[1]) * 60 + int(nums[2])
                    else: wait = 600
                    client.cooldown_glitch = wait + time.time()
                    client.logger.info(f'Glitch available ({datetime.timedelta(seconds=wait)})')
            elif 'not available' in msg.content: client.logger.info('Glitch not available')
        except asyncio.TimeoutError: client.logger.error('Glitch check timeout')