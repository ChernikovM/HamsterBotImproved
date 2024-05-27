import asyncio
from time import time
from random import randint
from urllib.parse import unquote

import datetime

import aiohttp
from aiohttp_proxy import ProxyConnector
from better_proxy import Proxy
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered
from pyrogram.raw.functions.messages import RequestWebView

from bot.config import settings
from bot.utils import logger
from bot.exceptions import InvalidSession
from .headers import headers
#from .user_agents import user_agents #add separate user agents for each account


class Tapper:
    def __init__(self, tg_client: Client):
        self.session_name = tg_client.name
        self.tg_client = tg_client

    async def get_tg_web_data(self, proxy: str | None) -> str:
        if proxy:
            proxy = Proxy.from_str(proxy)
            proxy_dict = dict(
                scheme=proxy.protocol,
                hostname=proxy.host,
                port=proxy.port,
                username=proxy.login,
                password=proxy.password
            )
        else:
            proxy_dict = None

        self.tg_client.proxy = proxy_dict

        try:
            if not self.tg_client.is_connected:
                try:
                    await self.tg_client.connect()
                except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                    raise InvalidSession(self.session_name)

            web_view = await self.tg_client.invoke(RequestWebView(
                peer=await self.tg_client.resolve_peer('hamster_kombat_bot'),
                bot=await self.tg_client.resolve_peer('hamster_kombat_bot'),
                platform='android',
                from_bot_menu=False,
                url='https://hamsterkombat.io/'
            ))

            auth_url = web_view.url
            tg_web_data = unquote(
                string=unquote(
                    string=auth_url.split('tgWebAppData=', maxsplit=1)[1].split('&tgWebAppVersion', maxsplit=1)[0]))

            if self.tg_client.is_connected:
                await self.tg_client.disconnect()

            return tg_web_data

        except InvalidSession as error:
            raise error

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error during Authorization: {error}")
            await asyncio.sleep(delay=3)

    async def login(self, http_client: aiohttp.ClientSession, tg_web_data: str) -> str:
        try:
            response = await http_client.post(url='https://api.hamsterkombat.io/auth/auth-by-telegram-webapp',
                                              json={"initDataRaw": tg_web_data, "fingerprint": {}})
            response.raise_for_status()

            response_json = await response.json()
            access_token = response_json['authToken']

            return access_token
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Access Token: {error}")
            await asyncio.sleep(delay=3)

    async def get_profile_data(self, http_client: aiohttp.ClientSession) -> dict[str]:
        try:
            response = await http_client.post(url='https://api.hamsterkombat.io/clicker/sync',
                                              json={})
            response.raise_for_status()

            response_json = await response.json()
            profile_data = response_json['clickerUser']

            return profile_data
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Profile Data: {error}")
            await asyncio.sleep(delay=3)

    async def get_tasks(self, http_client: aiohttp.ClientSession) -> dict[str]:
        try:
            response = await http_client.post(url='https://api.hamsterkombat.io/clicker/list-tasks',
                                              json={})
            response.raise_for_status()

            response_json = await response.json()
            tasks = response_json['tasks']

            return tasks
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Tasks: {error}")
            await asyncio.sleep(delay=3)

    async def select_exchange(self, http_client: aiohttp.ClientSession, exchange_id: str) -> bool:
        try:
            response = await http_client.post(url='https://api.hamsterkombat.io/clicker/select-exchange',
                                              json={'exchangeId': exchange_id})
            response.raise_for_status()

            return True
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while Select Exchange: {error}")
            await asyncio.sleep(delay=3)

            return False

    async def get_daily(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.post(url='https://api.hamsterkombat.io/clicker/check-task',
                                              json={'taskId': "streak_days"})
            response.raise_for_status()

            return True
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Daily: {error}")
            await asyncio.sleep(delay=3)

            return False

    async def apply_boost(self, http_client: aiohttp.ClientSession, boost_id: str) -> bool:
        try:
            response = await http_client.post(url='https://api.hamsterkombat.io/clicker/buy-boost',
                                              json={'timestamp': time(), 'boostId': boost_id})
            response.raise_for_status()

            return True
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while Apply {boost_id} Boost: {error}")
            await asyncio.sleep(delay=3)

            return False

    async def get_upgrades(self, http_client: aiohttp.ClientSession) -> list[dict]:
        try:
            response = await http_client.post(url='https://api.hamsterkombat.io/clicker/upgrades-for-buy',
                                              json={})
            response.raise_for_status()

            response_json = await response.json()
            upgrades = response_json['upgradesForBuy']

            return upgrades
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Upgrades: {error}")
            await asyncio.sleep(delay=3)
            
    async def get_boosts(self, http_client: aiohttp.ClientSession) -> list[dict]:
        try:
            response = await http_client.post(url='https://api.hamsterkombat.io/clicker/boosts-for-buy',
                                              json={})
            response.raise_for_status()

            response_json = await response.json()
            upgrades = response_json['boostsForBuy']

            return upgrades
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Upgrades: {error}")
            await asyncio.sleep(delay=3)

    async def buy_upgrade(self, http_client: aiohttp.ClientSession, upgrade_id: str) -> bool:
        try:
            response = await http_client.post(url='https://api.hamsterkombat.io/clicker/buy-upgrade',
                                              json={'timestamp': time(), 'upgradeId': upgrade_id})
            response.raise_for_status()

            return True
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while buying Upgrade: {error}")
            await asyncio.sleep(delay=3)

            return False

    async def send_taps(self, http_client: aiohttp.ClientSession, available_energy: int, taps: int, earn_per_tap: int) -> dict[str]:
        response_json = None
        request_json = None
        try:
            if taps > available_energy:
                taps = available_energy
                
            if available_energy - taps / earn_per_tap - 1 < settings.MIN_AVAILABLE_ENERGY:
                taps = available_energy - settings.MIN_AVAILABLE_ENERGY
                if taps < 1:
                    taps = 1
            
            count = int(taps / earn_per_tap - 1)
            
            if count < 1:
                count = 1
            
            request_json = {'availableTaps': available_energy, 'count': count, 'timestamp': int(time())}
            response = await http_client.post(
                url='https://api.hamsterkombat.io/clicker/tap',
                json= request_json)
            response.raise_for_status()

            response_json = await response.json()
            profile_data = response_json['clickerUser']

            return profile_data
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while Tapping: {error} | response_json: {response_json} | request_json: {request_json}")
            await asyncio.sleep(delay=3)

    async def check_proxy(self, http_client: aiohttp.ClientSession, proxy: Proxy) -> None:
        try:
            response = await http_client.get(url='https://httpbin.org/ip', timeout=aiohttp.ClientTimeout(5))
            ip = (await response.json()).get('origin')
            logger.info(f"{self.session_name} | Proxy IP: {ip}")
        except Exception as error:
            logger.error(f"{self.session_name} | Proxy: {proxy} | Error: {error}")

    async def run(self, proxy: str | None) -> None:
        access_token_created_time = 0
        turbo_time = 0
        active_turbo = False
        check_upgrades = True

        proxy_conn = ProxyConnector().from_url(proxy) if proxy else None

        async with (aiohttp.ClientSession(headers=headers, connector=proxy_conn) as http_client):
            if proxy:
                await self.check_proxy(http_client=http_client, proxy=proxy)

            boost_last_check = time() - 3800
            use_boost = False

            while True:
                try:
                    while True:
                        if time() - access_token_created_time >= 3600:
                            logger.warning(f"{self.session_name} | Authorization started")
                            tg_web_data = await self.get_tg_web_data(proxy=proxy)
                            access_token = await self.login(http_client=http_client, tg_web_data=tg_web_data)

                            http_client.headers["Authorization"] = f"Bearer {access_token}"
                            headers["Authorization"] = f"Bearer {access_token}"

                            access_token_created_time = time()
                            profile_data = None
                            
                        if not profile_data:
                            profile_data = await self.get_profile_data(http_client=http_client)
                            
                            if not profile_data:
                                logger.warning(f"{self.session_name} | Profile data broken, trying to fetch from tap request...")
                                
                                profile_data = await self.send_taps(http_client=http_client,
                                                           available_energy=1000,
                                                           taps=1,
                                                           earn_per_tap = 1)
                                                           
                                if not profile_data:
                                    logger.warning(f"{self.session_name} | Server is down, trying in 1 minute...")                      
                                    await asyncio.sleep(delay=60)
                                continue
                                
                            logger.success(f"{self.session_name} | Profile data loaded!")    
                                
                            exchange_id = profile_data.get('exchangeId')
                        
                            if not exchange_id:
                                status = await self.select_exchange(http_client=http_client, exchange_id="bybit")
                                if status is True:
                                    logger.success(f"{self.session_name} | Successfully selected exchange <y>Bybit</y>")

                            last_passive_earn = int(profile_data['lastPassiveEarn'])
                            earn_on_hour = profile_data['earnPassivePerHour']
                            earn_per_tap = profile_data['earnPerTap']

                            logger.info(f"{self.session_name} | Last passive earn: <g>+{last_passive_earn}</g> | "
                                        f"Earn every hour: <y>{earn_on_hour}</y>")

                            available_energy = profile_data['availableTaps']
                            balance = int(profile_data['balanceCoins'])

                            tasks = await self.get_tasks(http_client=http_client)

                            daily_task = tasks[-1]
                            rewards = daily_task['rewardsByDays']
                            is_completed = daily_task['isCompleted']
                            days = daily_task['days']
                            
                            if is_completed is False:
                                status = await self.get_daily(http_client=http_client)
                                if status is True:
                                    logger.success(f"{self.session_name} | Successfully get daily reward | "
                                                   f"Days: <m>{days}</m> | Reward coins: {rewards[days-1]['rewardCoins']}")
                            
                            break
                        break
                    
                    #if available_energy > settings.MIN_AVAILABLE_ENERGY:
                    taps = randint(a=settings.RANDOM_TAPS_COUNT[0], b=settings.RANDOM_TAPS_COUNT[1])
                    
                    if active_turbo:
                        taps += settings.ADD_TAPS_ON_TURBO
                        if time() - turbo_time > 20:
                            active_turbo = False
                            turbo_time = 0

                    profile_data = await self.send_taps(http_client=http_client,
                                                       available_energy=available_energy,
                                                       taps=taps,
                                                       earn_per_tap = earn_per_tap)

                    if not profile_data:
                        logger.info(f"{self.session_name} | <y>Sleeping 1 min...</y>")
                        await asyncio.sleep(delay=60)
                        continue

                    # REQUEST BASED CONSTANTS
                    available_energy = profile_data['availableTaps']
                    new_balance = int(profile_data['balanceCoins'])
                    calc_taps = new_balance - balance
                    balance = new_balance
                    total = int(profile_data['totalCoins'])
                    earn_on_hour = profile_data['earnPassivePerHour']
                    PLAYER_DATA_MAX_TAPS = profile_data['maxTaps']
                    PLAYER_DATA_TAPS_RECOVER_PER_SEC = profile_data['tapsRecoverPerSec']
                    PLAYER_DATA_EARN_PASSIVE_PER_HOUR = profile_data['earnPassivePerHour']
                    PLAYER_DATA_HOURLY_EARNINGS = 3600 * PLAYER_DATA_TAPS_RECOVER_PER_SEC + PLAYER_DATA_EARN_PASSIVE_PER_HOUR

                    #boosts = profile_data['boosts']
                    energy_boost_time = profile_data['boosts'].get('BoostFullAvailableTaps', {}).get('lastUpgradeAt', 0)
                    energy_boost_level = profile_data['boosts'].get('BoostFullAvailableTaps', {}).get('level', 0)

                    logger.success(f"{self.session_name} | Successful tapped! | "
                                   f"Balance: <c>{balance}</c> (<g>+{calc_taps}</g>) | Total: <e>{total}</e> | Farm: <g>{PLAYER_DATA_HOURLY_EARNINGS}</g><c>[{PLAYER_DATA_EARN_PASSIVE_PER_HOUR}]</c>")

                    if active_turbo is False:
                        
                        maxLevelEnergyBoost = 6
                        
                        if settings.APPLY_DAILY_ENERGY is True:
                            if time() - boost_last_check > 3650:
                                boosts = await self.get_boosts(http_client=http_client)
                                if boosts:
                                    boost_last_check = time()
                                    for item in boosts:
                                        if item.get("id") == "BoostFullAvailableTaps":
                                            fullTapsBoost = item
                                            maxLevelEnergyBoost = fullTapsBoost["maxLevel"]
                                            if fullTapsBoost["level"] < maxLevelEnergyBoost:    
                                                logger.info(f"{self.session_name} | <y>Boosts info: <b>{fullTapsBoost['level']}/{fullTapsBoost['maxLevel']}</b> | Next check: {datetime.datetime.fromtimestamp(boost_last_check + 3650).strftime('%H:%M:%S')}</y>")
                                                use_boost = True
                                            else:
                                                use_boost = False
                                                logger.info(f"{self.session_name} | <y>All boosts already used for today. Lets try after 6h</y>")
                                                boost_last_check = time() + 3600 * 5
                                            break    
                                else:
                                    logger.warning(f"{self.session_name} | <y>Boosts fetch is broken. Skipping...</y>")
                    
                        if (use_boost is True
                                and time() - energy_boost_time > 3600):
                                
                            logger.info(f"{self.session_name} | <y>Using full energy before boost apply...</y>")
                            await asyncio.sleep(delay=1)
                            profile_data = await self.send_taps(http_client=http_client,
                                                       available_energy=available_energy,
                                                       taps=available_energy,
                                                       earn_per_tap = earn_per_tap)
                            logger.info(f"{self.session_name} | <y>Applying boost...</y>")
                            await asyncio.sleep(delay=1)
                            status = await self.apply_boost(http_client=http_client, boost_id="BoostFullAvailableTaps")
                            if status is True:
                                logger.success(f"{self.session_name} | <g>Successfully applied energy boost</g>")
                                await asyncio.sleep(delay=3)
                                
                                profile_data = await self.send_taps(http_client=http_client,
                                                       available_energy=PLAYER_DATA_MAX_TAPS,
                                                       taps=PLAYER_DATA_MAX_TAPS,
                                                       earn_per_tap = earn_per_tap)
                                                       
                                if not profile_data:
                                    logger.warning(f"{self.session_name} | Something went wrong! Skipping...")
                                    continue
                                else:
                                    available_energy = profile_data['availableTaps']
                                    new_balance = int(profile_data['balanceCoins'])
                                    calc_taps = new_balance - balance
                                    balance = new_balance
                                    total = int(profile_data['totalCoins'])
                                    earn_on_hour = profile_data['earnPassivePerHour']
                                    PLAYER_DATA_MAX_TAPS = profile_data['maxTaps']
                                    PLAYER_DATA_TAPS_RECOVER_PER_SEC = profile_data['tapsRecoverPerSec']
                                    PLAYER_DATA_EARN_PASSIVE_PER_HOUR = profile_data['earnPassivePerHour']
                                    PLAYER_DATA_HOURLY_EARNINGS = 3600 * PLAYER_DATA_TAPS_RECOVER_PER_SEC + PLAYER_DATA_EARN_PASSIVE_PER_HOUR
                                    logger.success(f"{self.session_name} | Successful tapped! | "
                                                    f"Balance: <c>{balance}</c> (<g>+{calc_taps}</g>) | Total: <e>{total}</e> | Farm: <g>{PLAYER_DATA_HOURLY_EARNINGS}</g><c>[{PLAYER_DATA_EARN_PASSIVE_PER_HOUR}]</c>")
                            else:
                                logger.warnign(f"{self.session_name} | <y>Boost broken, skipping...</y>")

                            continue

                        if settings.AUTO_UPGRADE is True and check_upgrades is True:
                            upgrades = await self.get_upgrades(http_client=http_client)
                            available_upgrades = [upgrade for upgrade in upgrades if upgrade["isAvailable"] and not upgrade["isExpired"] and upgrade["level"] <= settings.MAX_LEVEL]
                            
                            while True:
                                best_upgrade = max(available_upgrades, key=lambda x: (x["profitPerHourDelta"] / x["price"]) if x["price"] != 0 else float('-inf'))
                                time_to_earn = best_upgrade["cooldownSeconds"] != 0 ? best_upgrade["cooldownSeconds"] : (best_upgrade["price"] - balance) / PLAYER_DATA_HOURLY_EARNINGS
                                time_to_return = int(best_upgrade["price"]/best_upgrade["profitPerHourDelta"])
                                logger.info(f"{self.session_name} | Best upgrade for now: <e>{best_upgrade['id']}</e> | <g>+{best_upgrade['profitPerHourDelta']}</g> | price:<b>{best_upgrade['price']}</b> | TTR: <b>{time_to_return}</b>")
                                await asyncio.sleep(delay=1)
                                
                                if best_upgrade['price'] / best_upgrade['profitPerHourDelta'] > settings.UPGRADE_MAX_RETURN_PERIOD_HOURS:
                                    logger.warning(f"{self.session_name} | <y>Upgrade return time [{int(best_upgrade['price'] / best_upgrade['profitPerHourDelta'])}] > [{settings.UPGRADE_MAX_RETURN_PERIOD_HOURS}] than maximum allowed. Cancelling checking upgrades...</y>")
                                    check_upgrades = False
                                    break
                                
                                if balance > best_upgrade['price']:
                                    status = await self.buy_upgrade(http_client=http_client, upgrade_id=best_upgrade['id'])
                                    if status is True:
                                        earn_on_hour += best_upgrade['profitPerHourDelta']
                                        logger.success(
                                            f"{self.session_name} | "
                                            f"Successfully upgraded <e>{best_upgrade['id']}</e> to <m>{best_upgrade['level']}</m> lvl | "
                                            f"Earn every hour: <y>{earn_on_hour}</y> (<g>+{best_upgrade['profitPerHourDelta']}</g>)")

                                        await asyncio.sleep(delay=1)
                                        break
                                    else:
                                        logger.warning(f"{self.session_name} | Upgrade declined by server. Skipping...")
                                        break
                                else:
                                    if time_to_earn > settings.MAX_EARNING_TIME_HOURS:
                                        logger.info(f"{self.session_name} | Time to earn greater than max allowed - continue looking for the best upgrade...")
                                        await asyncio.sleep(delay=1)
                                        available_upgrades = [upgrade for upgrade in available_upgrades if upgrade["price"] < best_upgrade['price']]
                                        
                                        if not available_upgrades:
                                            logger.info(f"{self.session_name} | No suitable upgrade found within the earning time limit. Try to increase limit or just wait for <g>$$$</g>.")
                                            break
                                    else:
                                        if time_to_earn >= 1:
                                            logger.info(f"{self.session_name} | Approximately time to earn: <e>{'{:.2f}'.format(time_to_earn)}</e> hour(s)")
                                        else:
                                            logger.info(f"{self.session_name} | Approximately time to earn: <e>{'{:.2f}'.format(time_to_earn*60)}</e> minute(s)")
                                        break

                        #if available_energy < settings.MIN_AVAILABLE_ENERGY:
                         #   logger.info(f"{self.session_name} | Minimum energy reached: {available_energy}")
                          #  logger.info(f"{self.session_name} | Sleep {settings.SLEEP_BY_MIN_ENERGY}s")
#
 #                           await asyncio.sleep(delay=settings.SLEEP_BY_MIN_ENERGY)
  #                          profile_data = None
#
 #                           continue

                except InvalidSession as error:
                    raise error

                except Exception as error:
                    logger.error(f"{self.session_name} | Unknown error: {error}")
                    await asyncio.sleep(delay=60)

                else:
                    sleep_between_clicks = randint(a=settings.SLEEP_BETWEEN_TAP[0], b=settings.SLEEP_BETWEEN_TAP[1])

                    if active_turbo is True:
                        sleep_between_clicks = 4

                    logger.info(f"{self.session_name} | Sleep {sleep_between_clicks}s")
                    await asyncio.sleep(delay=sleep_between_clicks)


async def run_tapper(tg_client: Client, proxy: str | None):
    try:
        await Tapper(tg_client=tg_client).run(proxy=proxy)
    except InvalidSession:
        logger.error(f"{tg_client.name} | Invalid Session")
