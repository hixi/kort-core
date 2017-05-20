from connexion import NoContent
from geoalchemy2 import Geometry
from sqlalchemy import extract
from sqlalchemy import func, Table, engine, update
from sqlalchemy import Date, cast

import json
import traceback

import api.models
from src.api.i18n import I18n
import datetime
from datetime import date

db_session = api.models.init_db()

def get_missions(lat, lon, radius, limit, lang):
    # print('get missions for language '+lang)
    # with open('data/missions.json') as json_data:
    #     d = json.load(json_data)
    #     return d
    try:
        q = db_session.query(api.models.kort_errors)\
        .order_by(api.models.kort_errors.geom.distance_box('POINT(' + str(lon) + ' ' + str(lat) + ')')) \
        .limit(limit)
        # .filter(api.models.kort_errors.geom.ST_Distance_Sphere('POINT(' + str(lon) + ' ' + str(lat) + ')') < radius) \

    except Exception as e:
        print(traceback.format_exc())
    return [p.dump(lang) for p in q][:limit]

def put_mission_solution(schema_id, error_id, lang, body):

    try:
        q = db_session.query(api.models.kort_errors).filter(api.models.kort_errors.errorId == error_id).filter(
            api.models.kort_errors.schema == schema_id)

        # 403 if user does not exist
        # TODO check if valid according to re,
        s = body['solution']

        user_id = s['userId']
        koins = s['koins']

        if q.count() == 1:
            # write solution to db
            new_solution = api.models.Solution(userId=user_id, create_date=datetime.datetime.utcnow(),
                                           error_id=error_id,
                                           schema=schema_id, osmId=s['osm_id'],
                                           solution=s['value'], complete=s['solved'],
                                           valid=True)
            db_session.add(new_solution)
            db_session.commit()


            # update koin count, mission count, missions today
            no_missions_today = db_session.query(api.models.Solution).\
                filter(api.models.Solution.user_id == user_id).\
                filter(cast(api.models.Solution.create_date,Date) == date.today()).\
                count()


            db_session.query(api.models.User).filter_by(id=user_id)\
                .update({api.models.User.koin_count: api.models.User.koin_count + koins,
                         api.models.User.mission_count: api.models.User.mission_count + 1,
                         api.models.User.mission_count_today: no_missions_today})
            db_session.commit()


            # get new badges for this user
            return create_new_achievements(user_id=user_id, solution=s, lang=lang)
        else:
            return NoContent, 404



    except Exception as e:
        print(traceback.format_exc())

    with open('data/achievements.json') as json_data:
        d = json.load(json_data)
        return d

def create_new_achievements(user_id, solution, lang):

    # no of missions
    q = db_session.query(api.models.Solution).filter(api.models.Solution.user_id == user_id)
    no_of_missions = q.count();
    print('no of missions', no_of_missions)


    # get user badges
    user_badge_ids = db_session.query(api.models.UserBadge.badge_id).filter(api.models.UserBadge.user_id == user_id)

    # get badges for this type which have not been achieved
    new_badges = db_session.query(api.models.Badge).\
        filter(api.models.Badge.name.like('fix_count_%')).\
        filter(api.models.Badge.compare_value <= no_of_missions).\
        filter(~api.models.Badge.id.in_(user_badge_ids))

    for row in new_badges:
        print(row.title)

    #insert badges
    badgesAchieved = []
    for badge in new_badges:
        db_session.add(
            api.models.UserBadge(user_id=user_id, badge_id=badge.id, create_date=datetime.datetime.utcnow())
        )
        badgesAchieved.append(badge.dump(lang, True, datetime.datetime.utcnow()))

    db_session.commit()

    return badgesAchieved

