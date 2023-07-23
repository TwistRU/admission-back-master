import re
import os
import json
from typing import List

import aiofiles
from pathlib import Path
from datetime import datetime
from Levenshtein import distance
from app.utils import (
    get_utc_date,
    convert_utc_to_local,
    get_latest_dump_date,
    strptime_to_utc,
    get_local_datetime
)


class MainPageCalculations:
    LATEST_DUMP_PATH = (Path(os.path.abspath(__file__))).parent.parent / 'data/latest.json'
    REGIONS_PATH = (Path(os.path.abspath(__file__))).parent.parent / 'data/regions_map.json'
    CAMPAIGN_TYPES = {
        'Прием на обучение на бакалавриат/специалитет': "Bachelor",
        'Прием на обучение в магистратуру': 'Magistracy',
        'Прием на обучение на СПО': 'SecVocEdu',
        'Прием на подготовку кадров высшей квалификации': 'HighQualified'
    }
    QUOTAS = {
        'На общих основаниях': 'BudgetQuota',
        'Целевой прием': 'TargetQuota',
        'Имеющие особое право': 'SpecialQuota',
        'Отдельная квота': 'SeparateQuota'
    }
    FINANCING = {
        'Полное возмещение затрат': 'FullCost',
        'Бюджетная основа': 'Budget'
    }
    SUPERSERVICE = 'Суперсервис \"Поступление в вуз онлайн\"'
    WEB = 'Веб'
    DOCUMENTDELIVERY = {SUPERSERVICE: 'SuperService', WEB: 'Web', 'Лично': 'Personal', 'Почта': 'Mail'}

    def __init__(self):
        pass

    async def _read_file(self, path):
        async with aiofiles.open(path, 'r', encoding='utf-8') as f:
            string = await f.read()
            return json.loads(string)

    async def get_main_page_data(self):
        self.dump = await self._read_file(self.LATEST_DUMP_PATH)
        self.result = dict()
        self.applications_total_data = await self._get_applications_agreements_total_data()
        self.average_ege_data = await self._get_average_ege_data()
        self.highballs_data = await self._get_highballs_data()
        self.applications_by_programs_data = await self._get_applications_by_programs_data()
        self.applications_by_region_data = await self._get_applications_by_region_data()
        self.last_update_date = await convert_utc_to_local(await get_latest_dump_date())

        return {
            'small_charts': await self._get_small_charts(),
            'applications_approval': await self._get_applications_approval(),
            'average_ege': await self._get_average_ege(),
            'highballs': await self._get_highballs(),
            'applications_by_programs': await self._get_applications_by_programs(),
            'applications_by_region': await self._get_applications_by_region(),
            'applicants': await self._get_applicants(),
            'last_update': datetime.strftime(self.last_update_date, '%Y-%m-%d %H:%M:%S'),
            'applicants_by_day': await self._get_applicants_by_day(),
        }

    async def _get_small_charts(self):
        return {
            'applications': {
                'data': [
                    {
                        'label': 2021,
                        'value': 27430
                    },
                    {
                        'label': 2022,
                        'value': 30000
                    },
                    {
                        'label': 2023,
                        'value': self.applications_total_data['applications_total']
                    }
                ],
                'range': '2021-2023',
                'total': self.applications_total_data['applications_total'],
                'today': self.applications_total_data['applications_today']
            },
            'applicants': {
                'data': [
                    {
                        'label': 2021,
                        'value': 10641
                    },
                    {
                        'label': 2022,
                        'value': 12045
                    },
                    {
                        'label': 2023,
                        'value': self.applications_total_data['applicants_total']
                    }
                ],
                'range': '2021-2023',
                'total': 0 + self.applications_total_data['applicants_total'],
                'today_online': self.applications_total_data['applicants_today_online'],
                'today_offline': self.applications_total_data['applicants_today_offline'],
            },
            'average': {
                'data': [
                    {
                        'label': 2018,
                        'value': 72.02
                    },
                    {
                        'label': 2019,
                        'value': 73.63
                    },
                    {
                        'label': 2020,
                        'value': 74.44
                    },
                    {
                        'label': 2021,
                        'value': 73.27
                    },
                    {
                        'label': 2022,
                        'value': 74.59
                    },
                    {
                        'label': 2023,
                        'value': self.average_ege_data['average_ege_total']
                    }
                ],
                'range': '2018-2023',
                'total': 0 + self.average_ege_data['average_ege_total'],
            },
            'approvals': {
                'total': self.applications_total_data['agreements_total'],
                'today': self.applications_total_data['agreements_today'],
            }
        }

    async def _get_applications_approval(self):
        result = []

        for date, value in sorted(
                self.applications_total_data['applications_by_day'].items(),
                key=lambda x: x[0]
        ):
            result.append({
                'type': 'Заявлений всего',
                'date': date.strftime('%d.%m.%Y'),
                'count': value
            })

        for date, value in sorted(
                self.applications_total_data['applications_offline_by_day'].items(),
                key=lambda x: x[0]
        ):
            result.append({
                'type': 'Заявлений c priem.dvfu.ru',
                'date': date.strftime('%d.%m.%Y'),
                'count': value
            })

        for date, value in sorted(
                self.applications_total_data['agreements_by_day'].items(),
                key=lambda x: x[0]
        ):
            result.append({
                'type': 'Оригиналов',
                'date': date.strftime('%d.%m.%Y'),
                'count': value
            })
        return result

    async def _get_average_ege(self):
        result = []
        for school, value in self.average_ege_data['average_ege_schools'].items():
            result.append({
                'school': school,
                'value': value
            })
        return result

    async def _get_highballs(self):
        result = []
        for school, value in self.highballs_data['school_highballs'].items():
            result.append({
                'school': school,
                'value': value
            })
        return result

    async def _get_applications_by_programs(self):
        result = {k: [] for k in self.CAMPAIGN_TYPES.values()}
        for program, value in self.applications_by_programs_data['applications_by_programs'].items():
            result[value[1]].append({
                'program': program,
                'value': value[0],
                'quotas': self.applications_by_programs_data["count_by_programs"][program],
                'ratings': self.applications_by_programs_data["ratings_by_programs"][program],
                'score': self.applications_by_programs_data["passing_score"][program]
            })
        for k in self.CAMPAIGN_TYPES.values():
            result[k].sort(key=lambda x: -x['value'])
        return result

    async def _get_applications_by_region(self):
        result = []
        for region, value in self.applications_by_region_data['applications_by_region'].items():
            if region:
                result.append({
                    'region': region,
                    'value': value
                })
        return result

    async def _get_applicants(self):
        return {
            'total': self.applications_total_data['applicants_total'],
            'today_online': self.applications_total_data['applicants_today_online'],
            'today_offline': self.applications_total_data['applicants_today_offline'],
        }

    async def _get_applicants_by_day(self):
        result = []
        for date, value in sorted(
                self.applications_total_data['applicants_by_day'].items(),
                key=lambda x: x[0]
        ):
            result.append({
                'type': 'Абитуриентов всего',
                'date': date.strftime('%d.%m.%Y'),
                'count': value
            })
        for date, value in sorted(
                self.applications_total_data['applicants_offline_by_day'].items(),
                key=lambda x: x[0]
        ):
            result.append({
                'type': 'Абитуриентов c priem.dvfu.ru',
                'date': date.strftime('%d.%m.%Y'),
                'count': value
            })
        for date, value in sorted(
                self.applications_total_data['applicants_online_by_day'].items(),
                key=lambda x: x[0]
        ):
            result.append({
                'type': 'Абитуриентов c Суперсервиса',
                'date': date.strftime('%d.%m.%Y'),
                'count': value
            })
        return result

    async def _get_applications_agreements_total_data(self):
        '''
            For speed purposes, we calculate this in single cycle.
        '''
        applications_info_today = {
            fs: {dd: {k: 0 for k in self.QUOTAS.values()} for dd in self.DOCUMENTDELIVERY.values()} for fs in
            self.FINANCING.values()}
        applications_info_total = {
            fs: {dd: {k: 0 for k in self.QUOTAS.values()} for dd in self.DOCUMENTDELIVERY.values()} for fs in
            self.FINANCING.values()}
        aplicants_info_today = {fs: {dd: {k: 0 for k in self.QUOTAS.values()} for dd in self.DOCUMENTDELIVERY.values()}
                                for fs in self.FINANCING.values()}
        aplicants_info_total = {fs: {dd: {k: 0 for k in self.QUOTAS.values()} for dd in self.DOCUMENTDELIVERY.values()}
                                for fs in self.FINANCING.values()}
        applications_by_day = dict()
        applications_web_by_day = dict()
        applicants_superservice_by_day = dict()
        applicants_web_by_day = dict()
        applicants_by_day = dict()
        applicants_used = set()

        agreements_by_day = dict()
        agreements_total = set()
        agreements_today = set()

        applicants_today_online = set()
        applicants_today_offline = set()
        applicants_total_online = set()
        applicants_total_offline = set()

        today_local = await get_local_datetime()
        for _, human_item in self.dump['data'].items():
            human = _
            for __, app_item in human_item.items():
                quota = self.QUOTAS[app_item['Category']]
                document_delivery = self.DOCUMENTDELIVERY[app_item['DocumentDelivery']]
                financing_source = self.FINANCING[app_item['FinancingSource']]
                item_date_download = await convert_utc_to_local(
                    await strptime_to_utc(app_item['firstDownloadDate'], '%Y-%m-%d %H:%M:%S')
                )
                item_date_local = item_date_download.replace(hour=0, minute=0, second=0, microsecond=0)

                if item_date_download.strftime('%Y-%m-%d') == today_local.strftime('%Y-%m-%d'):
                    applications_info_today[financing_source][document_delivery][quota] += 1
                    if document_delivery == self.WEB:
                        applicants_today_offline.add(human)
                    elif document_delivery == self.SUPERSERVICE:
                        applicants_today_online.add(human)
                    # TODO Переписать под оригиналы
                    if app_item['AtestOrig']:
                        agreements_today.add(human)

                applications_info_total[financing_source][document_delivery][quota] += 1
                if document_delivery == self.WEB:
                    applicants_total_offline.add(human)
                    if item_date_local in applications_web_by_day:
                        applications_web_by_day[item_date_local] += 1
                    else:
                        applications_web_by_day[item_date_local] = 1

                elif document_delivery == self.SUPERSERVICE:
                    applicants_total_online.add(human)
                if app_item['AtestOrig']:
                    # TODO Согласие заменить на оригиналы
                    agreements_total.add(human)
                    if item_date_local in agreements_by_day:
                        agreements_by_day[item_date_local].add(human)
                    else:
                        agreements_by_day[item_date_local] = set()

                if item_date_local in applications_by_day:
                    applications_by_day[item_date_local] += 1
                else:
                    applications_by_day[item_date_local] = 1

                if human not in applicants_used:
                    if document_delivery == "Веб":
                        applicants_web_by_day[item_date_local] = applicants_web_by_day.get(item_date_local,
                                                                                           0) + 1
                    elif document_delivery == "Суперсервис \"Поступление в вуз онлайн\"":
                        applicants_superservice_by_day[item_date_local] = applicants_superservice_by_day.get(
                            item_date_local, 0) + 1
                    applicants_used.add(human)

        applications_today = 0  # {k: sum(v.values()) for k, v in applications_info_today.items()}
        applications_total = 0  # {k: sum(v.values()) for k, v in applications_info_total.items()}

        applicants_today = applicants_today_offline | applicants_today_online
        applicants_total = applicants_total_offline | applicants_total_online

        applicants_by_day = applicants_web_by_day.copy()
        for date, value in applicants_superservice_by_day.items():
            applicants_by_day[date] = applicants_by_day.get(date, 0) + value
        agreements_by_day = {k: len(v) for k, v in agreements_by_day.items()}

        return {
            'applications_today': applications_info_today,
            'applications_total': applications_info_total,
            'agreements_today': len(agreements_today),
            'agreements_total': len(agreements_total),
            'agreements_by_day': agreements_by_day,
            'applications_by_day': applications_by_day,
            'applications_offline_by_day': applications_web_by_day,
            'applicants_today': len(applicants_today),
            'applicants_today_online': len(applicants_today_online),
            'applicants_today_offline': len(applicants_today_offline),
            'applicants_total': len(applicants_total),
            'applicants_total_online': len(applicants_total_online),
            'applicants_total_offline': len(applicants_total_offline),
            'applicants_online_by_day': applicants_superservice_by_day,
            'applicants_offline_by_day': applicants_web_by_day,
            'applicants_by_day': applicants_by_day,
        }

    async def _get_average_ege_data(self):
        average_ege_total = 0
        average_ege_num = 0
        average_ege_school = dict()

        used_total = dict()
        used_school = dict()
        for _, human_item in self.dump['data'].items():
            for __, app_item in human_item.items():
                if app_item['FinancingSource'] != 'Бюджетная основа':
                    continue

                human = app_item['Code']
                # TODO Сделать по школам
                # school = item['IP_PROP1643']
                # if human not in used_total:
                #     used_total[human] = set()
                # if school not in used_school:
                #     used_school[school] = dict()
                #     used_school[school][human] = set()
                #     average_ege_school[school] = {
                #         'total': 0,
                #         'num': 0,
                #     }
                # if human not in used_school[school]:
                #     used_school[school][human] = set()

                # TODO Доделать когда будет знак Test1IsEGE
                for code in range(4):
                    score = app_item[f"Test{code + 1}Score"]
                    if score > 0:
                        average_ege_total += score
                        average_ege_num += 1
                        # TODO Сделать по школам
                        # if subject_name not in used_school[school][human]:
                        #     used_school[school][human].add(subject_name)
                        #     average_ege_school[school]['total'] += score
                        #     average_ege_school[school]['num'] += 1
        for key in average_ege_school:
            try:
                average_ege_school[key] = average_ege_school[key]['total'] / average_ege_school[key]['num']
            except Exception:
                average_ege_school[key] = 0
        return {
            'average_ege_total': average_ege_total / average_ege_num if average_ege_num > 0 else 0,
            'average_ege_schools': average_ege_school,
        }

    async def _get_highballs_data(self):
        school_highballs = dict()
        # TODO Сделать по школам
        # for _, item in self.dump['data'].items():
        #     human = item['Code']
        #     school = item['IP_PROP1643']
        #     if school not in school_highballs:
        #         school_highballs[school] = set()
        #     if human in school_highballs[school]:
        #         continue
        #     sum_balls = await self._get_sum_balls(item)
        #     if sum_balls >= 270:
        #         school_highballs[school].add(human)
        # for school in school_highballs:
        #     school_highballs[school] = len(school_highballs[school])
        return {
            'school_highballs': school_highballs
        }

    async def _get_sum_balls(self, item):
        sum_balls = 0
        # TODO Доделать когда будет знак Test1IsEGE
        if item["NoExams"]:
            return 0
        for code in range(item["ExamsCount"]):
            score = item[f"Test{code + 1}Score"]
            if score > 0:
                sum_balls += score
        return sum_balls

    async def _get_applications_by_programs_data(self):
        count_by_programs = dict()
        applications_by_programs = dict()
        for _, human_item in self.dump['data'].items():
            for __, app_item in human_item.items():
                program = app_item['TrainingDirection']
                if program not in count_by_programs:
                    count_by_programs[program] = dict()
                    count_by_programs[program]["BudgetQuotaCount"] = app_item["BudgetQuotaCount"]
                    count_by_programs[program]["TargetQuotaCount"] = app_item["TargetQuotaCount"]
                    count_by_programs[program]["SpecialQuotaCount"] = app_item["SpecialQuotaCount"]
                    count_by_programs[program]["SeparateQuotaCount"] = app_item["SeparateQuotaCount"]
                if program not in applications_by_programs:
                    applications_by_programs[program] = [0, self.CAMPAIGN_TYPES[app_item['AdmissionCampaignType']]]
                applications_by_programs[program][0] += 1
        return {
            'applications_by_programs': applications_by_programs,
            'count_by_programs': count_by_programs,
            'ratings_by_programs': await self._get_ratings_by_programs(),
            'passing_score': await self._get_passing_score_by_programs()
        }

    async def _get_ratings_by_programs(self):
        applications_by_programs = dict()
        info_by_programs = dict()
        for _, human_item in self.dump['data'].items():
            for __, app_item in human_item.items():
                program = app_item['TrainingDirection']
                quota = self.QUOTAS[app_item['Category']]
                if program not in applications_by_programs:
                    applications_by_programs[program] = dict()
                    info_by_programs[program] = {k: [0, 0] for k in self.QUOTAS.values()}
                if quota not in applications_by_programs[program]:
                    applications_by_programs[program][quota] = []
                applications_by_programs[program][quota].append(app_item)
                if app_item['SelectedPriority'] == 1:
                    if app_item['AtestOrig']:
                        info_by_programs[program][quota][1] += 1
                    else:
                        info_by_programs[program][quota][0] += 1
        return info_by_programs

    async def _get_passing_score_by_programs(self):
        applications_by_programs = dict()
        info_by_programs = dict()
        for _, human_item in self.dump['data'].items():
            for __, app_item in human_item.items():
                program = app_item['TrainingDirection']
                quota = self.QUOTAS[app_item['Category']]
                if program not in applications_by_programs:
                    applications_by_programs[program] = {k: [[], 0] for k in self.QUOTAS.values()}
                    info_by_programs[program] = {k: 0 for k in self.QUOTAS.values()}
                if app_item['SelectedPriority'] == 1 and app_item['AtestOrig'] and not app_item['NoExams']:
                    applications_by_programs[program][quota][0].append(app_item)
                if app_item['AtestOrig'] and app_item['NoExams']:
                    applications_by_programs[program][quota][1] += 1

        for program, quotas in applications_by_programs.items():
            for quota, applications in quotas.items():
                apps: List = applications[0].copy()
                apps.sort(key=lambda x: x['SumScore'], reverse=True)
                if len(apps) > 0:
                    kcp = apps[0][quota + "Count"] - applications[1]
                    last = len(apps)
                    info_by_programs[program][quota] = apps[min(kcp, last) - 1]['SumScore']

        return info_by_programs

    async def _get_applications_by_region_data(self):
        regions_map = await self._read_file(self.REGIONS_PATH)

        regexp_list = [
            r"\s*область\s*",
            r"\s+обл\s*",
            r"\s*край\s*",
            r"\s*республика\s*",
            r"\s+респ\s*",
            r"\s+г\s*",
            r"\s+аобл\s*",
            r"\s+ао\s*",
            r"\s*автономная область\s*",
            r"\s*автономный округ\s*",
        ]

        def clear_region(str):
            result = str.lower()

            for reg_exp in regexp_list:
                result = re.sub(reg_exp, "", result)

            return result

        def find_best_match(adress):
            best_match = None

            if not adress:
                return best_match

            min_dist = float("inf")

            for reg, iso_code in regions_map.items():
                dist = distance(reg, adress)
                if dist < min_dist:
                    min_dist = dist
                    best_match = iso_code

            return best_match if min_dist < 10 else None

        applications_by_region = dict()

        for _, human_item in self.dump['data'].items():
            ad = list(human_item.values())[0]['AdmissionCampaignType']
            if ad != "Прием на обучение на бакалавриат/специалитет":
                continue
            region = clear_region(list(human_item.values())[0]['Region'])
            iso_code = find_best_match(region)

            if iso_code not in applications_by_region:
                applications_by_region[iso_code] = 0
            applications_by_region[iso_code] += 1

        return {
            'applications_by_region': applications_by_region
        }
