import requests
import time
import pandas as pd

from sqlalchemy import create_engine
from tqdm.notebook import tqdm


class GetLolGameAccountInfo ():

    def __init__(self, api_key):
        self.api_key = api_key
        self.engine = create_engine("mysql+pymysql://test:"+"test1"+"@14.49.45.15:3306/sumin?charset=utf8",
                                    encoding='utf-8')

    def get_game_id(self, account_id_list):
        params = {'api_key': self.api_key}
        count = 0

        # engine = create_engine("mysql+pymysql://test:"+"test1"+"@14.49.45.15:3306/sumin?charset=utf8",
        #                        encoding='utf-8')
        conn = self.engine.connect()
        game_id_total_list = []
        for account_id in tqdm(account_id_list):
            game_id_list = []
            match_2_url = "https://kr.api.riotgames.com/lol/match/v4/matchlists/by-account/" + account_id
            match_2_info = requests.get(match_2_url, params=params)
            match_2_rank = match_2_info.json()
            try:
                for v in match_2_rank['matches']:
                    if v['queue'] == 420:
                        game_id_list.append(v['gameId'])
                    else:
                        continue
            except:
                time.sleep(120)
            time.sleep(2)
            game_id_total_list.append(game_id_list)
            data = pd.DataFrame(game_id_list).rename({0: "game_id"}, axis=1)
            data.to_sql(name='game_id', con=self.engine,
                        if_exists='append', index=False)

        conn.close()
        return game_id_total_list

    def get_account_id(self, game_id_list):

        params = {'api_key': self.api_key}
        count = + 0
        df_list = []
        for id_ in tqdm(game_id_list):
            account_info_list = []
            time.sleep(1)
            count += 1
            if count % 9 == False:
                time.sleep(130)

            match_1_url = "https://kr.api.riotgames.com/lol/match/v4/matches/" + \
                str(id_)
            match_1_info = requests.get(match_1_url, params=params)
            match_1_rank = match_1_info.json()

            try:
                for v in match_1_rank['participantIdentities']:
                    account_info_list.append(
                        {"game_id": id_,
                         "summoner_id": v['player']['summonerId'],
                         "account_id": v['player']['accountId'],
                         "game_nickname": v['player']['summonerName'],
                         "currentAccountId": v['player']['currentAccountId'],
                         "currentPlatformId": v['player']['currentPlatformId']
                         })
            except:
                return account_info_list

            game_tier_list = []
            for summoner_id in [v['summoner_id'] for v in account_info_list]:
                summoner_url = "https://kr.api.riotgames.com/lol/league/v4/entries/by-summoner/"+summoner_id
                summoner_info = requests.get(summoner_url, params=params)
                summoner_data = summoner_info.json()
                for i in summoner_data:
                    game_tier_dic = {}
                    try:
                        if i['queueType'] == 'RANKED_SOLO_5x5':
                            game_tier_dic['leaguePoints'] = i['leaguePoints']
                            game_tier_dic['wins'] = i['wins']
                            game_tier_dic['losses'] = i['losses']
                            game_tier_dic['veteran'] = i['veteran']
                            game_tier_dic['inactive'] = i['inactive']
                            game_tier_dic['freshBlood'] = i['freshBlood']
                            game_tier_dic['hotStreak'] = i['hotStreak']
                            game_tier_dic['tier'] = i['tier']
                            game_tier_dic['tier_rank'] = i['rank']
                            game_tier_dic["summoner_id"] = summoner_id
                            game_tier_list.append(game_tier_dic)
                        else:
                            continue
                    except:
                        return account_info_list, game_tier_list

            df = pd.DataFrame(account_info_list).merge(
                pd.DataFrame(game_tier_list), on="summoner_id", how="outer").fillna(-1).drop_duplicates()

            df.to_sql(name='user_id', con=self.engine,
                      if_exists='append', index=False)
            df_list.append(df)

        return df_list
