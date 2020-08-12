# 라이브러리
import requests
import pandas as pd
import numpy as np
import time
import urllib.request, json

import warnings
warnings.filterwarnings('ignore')

def search_detail_log(api_key, match_id): # API 2번 사용

    # API 키 등록
    params = {'api_key': api_key}

    # match_id 활용해 data추출 시작
    match_info_url = "https://kr.api.riotgames.com/lol/match/v4/matches/" + "{}".format(match_id)
    match_info = requests.get(match_info_url, params=params)
    match = match_info.json()

    # 밴 리스트 추출
    ban_raw_list = []
    for i in match['teams']:
        for j in i['bans']:
            ban_raw_list.append(j['championId'])

    ban_list = []
    for i in ban_raw_list:
        if i == -1:
            ban_list.append(-1) # 밴을 하지 않을 경우 -1
        else:
            ban_list.append(i)

    # summonerId 추출
    user_id_dic = {}
    for i in match['participantIdentities']:
        user_id_dic[i['participantId']] = i['player']['summonerId']

    # game data 추출출
    game_data = []
    for i in match['participants']:
        each_user = []
        for j in ['teamId', 'championId', 'spell1Id', 'spell2Id', 'stats', 'timeline']:
            if j == 'championId':
                each_user.append(i[j])
            elif (j == 'spell1Id') or (j == 'spell2Id'):
                each_user.append(i[j])
            elif j == 'stats':
                each_user.append(i[j]['participantId'])
                each_user.append(i[j]['win'])
                each_user.append(i[j]['kills'])
                each_user.append(i[j]['deaths'])
                each_user.append(i[j]['assists'])
                each_user.append(i[j]['totalMinionsKilled'])
            elif j == 'timeline':
                each_user.append(i[j]['role'])
                each_user.append(i[j]['lane'])
            else:
                each_user.append(i[j])
        game_data.append(each_user)

    game_data_df = pd.DataFrame(game_data)
    game_data_df.columns = ['team_position', 'champion', 'spell_1', 'spell_2', 'id', 'game_result', 'kill', 'death',
                            'assist', 'cs', '역할', '라인']
    game_data_df['game_result'] = [1 if i == True else 0 for i in game_data_df['game_result']]
    game_data_df['summoner_id'] = [user_id_dic[i] for i in game_data_df['id']]

    game_data_df['ban_champion'] = ban_list
    game_data_df = game_data_df.set_index('id')

    # 라인 셋팅하기 위해 timeline api 사용
    match_timeline_url = "https://kr.api.riotgames.com/lol/match/v4/timelines/by-match/{}".format(match_id)
    match_timeline_info = requests.get(match_timeline_url, params=params)
    match_timeline = match_timeline_info.json()

    match_timeline_id = []
    match_timeline_x_position = []
    match_timeline_y_position = []
    for i in match_timeline['frames'][2:7]:
        for j in i['participantFrames']:
            match_timeline_id.append(i['participantFrames']['{}'.format(j)]['participantId'])
            match_timeline_x_position.append(i['participantFrames']['{}'.format(j)]['position']['x'])
            match_timeline_y_position.append(i['participantFrames']['{}'.format(j)]['position']['y'])

    position_df = pd.DataFrame([match_timeline_id, match_timeline_x_position, match_timeline_y_position]).T
    position_df.columns = ['Id', 'x_position', 'y_position']

    x_mean_list = []
    y_mean_list = []
    std_list = []
    for i in range(1, 11):
        position_id_df = position_df[position_df['Id'] == i]
        x_mean = np.mean(position_id_df['x_position'])
        y_mean = np.mean(position_id_df['y_position'])
        x_std = np.std(position_id_df['x_position'])
        y_std = np.std(position_id_df['y_position'])
        x_mean_list.append(x_mean)
        y_mean_list.append(y_mean)
        std_list.append(round(np.sqrt((x_std) ** 2 + (y_std) ** 2), 2))

    game_data_df['y_mean'] = y_mean_list
    game_data_df['std'] = std_list

    result_victory_df = game_data_df[game_data_df['game_result'] == 1]
    result_victory_df = result_victory_df.sort_values(by='y_mean', ascending=False)
    result_victory_df['lane'] = [1, '', '', '', '']

    if '11' in list(result_victory_df.iloc[1, 2:4]):
        result_victory_df.iloc[1, -1] = 2
        result_victory_df.iloc[2, -1] = 3
    else:
        result_victory_df.iloc[1, -1] = 3
        result_victory_df.iloc[2, -1] = 2

    if result_victory_df.iloc[3, 8] > result_victory_df.iloc[4, 8]:
        result_victory_df.iloc[3, -1] = 4
        result_victory_df.iloc[4, -1] = 5
    else:
        result_victory_df.iloc[3, -1] = 5
        result_victory_df.iloc[4, -1] = 4

    result_defeat_df = game_data_df[game_data_df['game_result'] == 0]
    result_defeat_df = result_defeat_df.sort_values(by='y_mean', ascending=False)
    result_defeat_df['lane'] = [1, '', '', '', '']

    if '11' in list(result_defeat_df.iloc[1, 2:4]):
        result_defeat_df.iloc[1, -1] = 2
        result_defeat_df.iloc[2, -1] = 3
    else:
        result_defeat_df.iloc[1, -1] = 3
        result_defeat_df.iloc[2, -1] = 2

    if result_defeat_df.iloc[3, 8] > result_defeat_df.iloc[4, 8]:
        result_defeat_df.iloc[3, -1] = 4
        result_defeat_df.iloc[4, -1] = 5
    else:
        result_defeat_df.iloc[3, -1] = 5
        result_defeat_df.iloc[4, -1] = 4

    # 승리, 패배 데이터를 나눠 라인 정의의
    result_victory_df = result_victory_df.sort_values(by='lane')
    result_defeat_df = result_defeat_df.sort_values(by='lane')

    final_edit_df = pd.concat([result_victory_df,result_defeat_df]).reset_index()

    final_edit_df['game_id'] = match_id
    final_edit_df = final_edit_df[['game_id', 'summoner_id', 'team_position', 'game_result', 'champion', 'spell_1',
                                   'spell_2', 'kill', 'death', 'assist', 'lane', 'cs', 'ban_champion']]

    return final_edit_df
