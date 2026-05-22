"""
Gem management: use gems (couple/single), open boxes, check glitch.
Includes no_gem flag to prevent spam when out of gems.
"""

import asyncio
import re
import random
import time
import datetime

class Gem:
    GEM_TIERS = {
        'gem1': range(51, 58),
        'gem3': range(65, 72),
        'gem4': range(72, 79),
        'star': range(79, 86),
    }

    # ---------- Helper: send use command & handle special pet ----------
    @staticmethod
    async def _send_use(client, gem_str):
        if not gem_str:
            return
        await client.current_channel.send(f'{client.prefix}use {gem_str}')
        client.logger.info(f'Sent {client.prefix}use {gem_str}')
        # Success: we used a gem, so no_gem flag is cleared
        client.no_gem = False
        try:
            msg = await client.wait_for(
                'message',
                check=lambda m: (
                    client.is_owo_message(m, in_channel=True)
                    and client.msg_contains(m, all_of=[str(client.nickname), 'active Special gem or you do not own'])
                ),
                timeout=10
            )
            client.special_pet_available = False
        except asyncio.TimeoutError:
            pass

    # ---------- Inventory ----------
    @staticmethod
    async def get_inventory(client):
        await asyncio.sleep(random.uniform(2, 3))
        if not client.current_channel:
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
                timeout=10,
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

    # ---------- Public entry point ----------
    @staticmethod
    async def use_gem(client):
        cfg = client.config['gem']
        if not cfg['use']:
            return
        if cfg['couple']:
            await Gem._couple_gem(client, cfg)
        else:
            await Gem._single_gem(client, cfg, tiers_to_use=None)

    # ---------- Couple gem (from old.py) ----------
    @staticmethod
    async def _couple_gem(client, cfg):
        # If we already know there are no gems, skip with a cooldown
        if getattr(client, 'no_gem', False):
            # Reset no_gem after 5 minutes (to re-check)
            if getattr(client, 'no_gem_since', 0) + 300 < time.time():
                client.no_gem = False
            else:
                return

        inv = await Gem.get_inventory(client)
        if not inv:
            return

        tiers = {'gem1': range(51, 58), 'gem3': range(65, 72), 'gem4': range(72, 79)}
        if cfg['star'] and getattr(client, 'special_pet_available', False):
            tiers['star'] = range(79, 86)

        start = {'gem1': 51, 'gem3': 65, 'gem4': 72, 'star': 79}
        active = [k for k in tiers if k in start]
        if not active:
            return

        max_n = min(tiers[k].stop - start[k] for k in active)
        valid = []
        for n in range(max_n):
            combo = [start[k] + n for k in active]
            if all(c in inv and c in tiers[k] for c, k in zip(combo, active)):
                valid.append(combo)

        if not valid:
            # No gems available -> set no_gem flag and record time
            client.no_gem = True
            client.no_gem_since = time.time()
            client.logger.info('No couple gems available, disabling further attempts for 5 min')
            return

        selected = valid[-1] if cfg['best'] else valid[0]
        await Gem._send_use(client, ' '.join(map(str, selected)))

    # ---------- Single gem (unified) ----------
    @staticmethod
    async def _single_gem(client, cfg, tiers_to_use=None):
        if getattr(client, 'no_gem', False):
            if getattr(client, 'no_gem_since', 0) + 300 < time.time():
                client.no_gem = False
            else:
                return

        inv = await Gem.get_inventory(client)
        if not inv:
            return

        if tiers_to_use is None:
            all_tiers = ['gem1', 'gem3', 'gem4']
            if cfg['star'] and getattr(client, 'special_pet_available', False):
                all_tiers.append('star')
            tiers_to_use = all_tiers

        gems = []
        for tier in tiers_to_use:
            if tier == 'star' and not (cfg['star'] and getattr(client, 'special_pet_available', False)):
                continue
            tier_range = Gem.GEM_TIERS.get(tier)
            if not tier_range:
                continue
            available = [g for g in inv if g in tier_range]
            if available:
                selected = max(available) if cfg['best'] else min(available)
                gems.append(str(selected))

        if gems:
            await Gem._send_use(client, ' '.join(gems))
        else:
            # No gems found
            client.no_gem = True
            client.no_gem_since = time.time()
            client.logger.info(f'No {tiers_to_use} gems available, disabling further attempts for 5 min')

    # ---------- Check gem after catching (triggered by message) ----------
    @staticmethod
    async def check_gem(client, message):
        if not getattr(client, 'selfbot_running', False):
            return
        if not client.is_owo_message(message, in_channel=True):
            return
        if not client.msg_contains(message, all_of=[str(client.nickname), '🌱', 'gained']):
            return

        cfg = client.config['gem']
        if not cfg['use']:
            return

        # If no_gem flag is active, skip checking
        if getattr(client, 'no_gem', False):
            # Auto-reset after 5 minutes
            if getattr(client, 'no_gem_since', 0) + 300 < time.time():
                client.no_gem = False
            else:
                return

        if cfg['couple']:
            if 'spent 5 <:cowoncy:416043450337853441> and caught a' in message.content:
                await Gem._couple_gem(client, cfg)
        else:
            inv_text = getattr(client, 'inventory_str', '')
            empty = []
            for tier in ['gem1', 'gem3', 'gem4', 'star']:
                if tier not in message.content and tier in inv_text:
                    empty.append(tier)
            if empty:
                await Gem._single_gem(client, cfg, tiers_to_use=empty)

    # ---------- Glitch ----------
    @staticmethod
    def glitch_available(client):
        cfg = client.config['gem']
        if not cfg.get('glitch', False):
            return False
        if getattr(client, 'cooldown_glitch', 0) - time.time() > 0:
            return False
        if not getattr(client, 'glitch_loop_ran', True):
            return False
        return True

    @staticmethod
    async def check_glitch(client):
        if not Gem.glitch_available(client):
            return
        if not client.current_channel:
            return
        await client.current_channel.send(f'{client.prefix}dt')
        client.logger.info(f'Sent {client.prefix}dt')
        try:
            msg = await client.wait_for(
                'message',
                check=lambda m: (
                    client.is_owo_message(m, in_channel=True)
                    and client.msg_contains(m, any_of=['are available', 'not available'])
                ),
                timeout=10,
            )
            if 'are available' in msg.content:
                parts = re.findall(r'\*\*(.*?)\*\*', msg.content)
                if len(parts) >= 3:
                    nums = re.findall(r'[0-9]+', parts[2])
                    if len(nums) == 1:
                        wait = int(nums[0])
                    elif len(nums) == 2:
                        wait = int(nums[0]) * 60 + int(nums[1])
                    elif len(nums) >= 3:
                        wait = int(nums[0]) * 3600 + int(nums[1]) * 60 + int(nums[2])
                    else:
                        wait = 600
                    client.cooldown_glitch = wait + time.time()
                    client.logger.info(f'Glitch available ({datetime.timedelta(seconds=wait)})')
            elif 'not available' in msg.content:
                client.logger.info('Glitch not available')
        except asyncio.TimeoutError:
            client.logger.error('Glitch check timeout')