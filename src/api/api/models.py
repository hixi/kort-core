import os
import sys
import json
from sqlalchemy import Column, DateTime, String, Integer, BigInteger, Boolean, create_engine, UniqueConstraint, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from geoalchemy2 import Geometry

from config.config import BaseConfig

import datetime

from .missionTypes import MissionTypes

Base = declarative_base()

class User(Base):

    __tablename__ = 'user'
    __table_args__ = {'schema': 'kort'}

    id                  = Column('user_id', Integer, primary_key=True)
    secret              = Column(String, nullable=False, unique=True)
    koin_count          = Column(Integer, nullable=False)
    name                = Column(String, nullable=False)
    username            = Column(String, nullable=False)
    oauth_provider      = Column(String, nullable=False)
    oauth_user_id       = Column(String, nullable=False)
    pic_url             = Column(String, nullable=True)
    token               = Column(String, nullable=True)
    mission_count       = Column(Integer, nullable=False)
    mission_count_today = Column(Integer, nullable=False)
    logged_in           = Column(Boolean, nullable=False)
    last_login          = Column(DateTime, nullable=False)
    UniqueConstraint(oauth_provider, oauth_user_id, name='unique_oauth_user')

    def __init__(self, name, username, oauth_provider, oauth_user_id, pic_url, secret, token):
        self.mission_count = 0
        self.mission_count_today = 0
        self.koin_count = 0
        self.name = name
        self.username = username
        self.oauth_provider = oauth_provider
        self.oauth_user_id = oauth_user_id
        self.pic_url = pic_url
        self.secret = secret
        self.token = token
        self.logged_in = True
        self.last_login = datetime.datetime.utcnow()

    def update(self, id=None, name=None, username=None,
               last_login=None, pic_url=None, token=None,
               logged_in=None, secret=None, oauth_provider=None,
               oauth_user_id=None, mission_count=None, mission_count_today=None, koin_count=None):
        if name is not None:
            self.name = name
        if username is not None:
            self.username = username
        if last_login is not None:
            self.last_login = last_login

    def dump(self):
        return dict([(k, v) for k, v in vars(self).items() if not k.startswith('_')])

    def __str__(self):
        return str(self.dump())

class Mission(Base):

    __tablename__ = 'missions'
    __table_args__ = {'schema': 'kort'}

    error_id                = Column(Integer, primary_key=True)
    schema                  = Column(String, primary_key=True)
    type                    = Column(Integer, nullable=False)
    geom                    = Column(Geometry, nullable=False)
    geo_json                 = Column(String, nullable=False)
    osm_id                   = Column(BigInteger, primary_key=True)
    osm_type                 = Column(String, nullable=False)

    def __init__(self, error_id, schema, type, geom, geo_json, osm_id, osm_type):
        self.error_id = error_id
        self.schema = schema
        self.type = type
        self.osm_id = osm_id
        self.osm_type = osm_type
        self.geom = geom
        self.geo_json = geo_json

    def dump(self):
        d = dict([(k, v) for k, v in vars(self).items() if not k.startswith('_') and not k == 'geom'])

        postgis2mapboxGeometry = {'Point': 'point', 'LineString': 'line'}
        geoJSON = json.loads(d['geo_json'])

        d['id'] = 'kr'+str(d['schema'])+'-'+str(d['error_id'])
        d['coordinates'] = [geoJSON['coordinates'][1], geoJSON['coordinates'][0]]
        d['annotationCoordinate'] = [geoJSON['coordinates'][1], geoJSON['coordinates'][0]]
        d['geomType'] = postgis2mapboxGeometry[geoJSON['type']]

        mt = MissionTypes()
        d['inputType'] = mt.getInputType(d['type'])
        d['question'] = mt.getQuestion(d['type'])
        d['image'] = mt.getImage(d['type'])
        d['title'] = mt.getTitle(d['type'])
        d['type'] = mt.getType(d['type'])
        d['koinReward'] = 1
        return d

class kort_errors(Base):

    __table_args__ = {'schema': 'kort'}
    __tablename__ = 'errors'

    id                      = Column(Integer, primary_key=True)
    schema                  = Column(String, primary_key=False)
    type                    = Column(String, primary_key=False)
    osmId                   = Column('osm_id', BigInteger, primary_key=False)
    osmType                 = Column('osm_type', String, primary_key=False)
    title                   = Column(String, primary_key=False)
    view_type               = Column(String, primary_key=False)
    answer_placeholder      = Column(String, primary_key=False)
    description             = Column(String, primary_key=False)
    fix_koin_count          = Column(Integer, primary_key=False)
    geom                    = Column(Geometry, nullable=False)
    latitude                = Column(Numeric, primary_key=False)
    longitude               = Column(Numeric, primary_key=False)


    def dump(self):
        d = dict([(k, v) for k, v in vars(self).items() if not k.startswith('_') and not k == 'geom'])
        d['id'] = 's'+str(d.pop('schema'))+'id'+str(d.pop('id'))
        d['annotationCoordinate'] = [float(d.pop('latitude')), float(d.pop('longitude'))]
        d['geomType'] = 'point' if d['osmType'] == 'node' else 'line'
        d['koinReward'] = d.pop('fix_koin_count')

        mt = MissionTypes()
        d['inputType'] = mt.getInputType(d['type'])
        d['question'] = mt.getQuestion(d['type'])
        d['image'] = mt.getImage(d['type'])

        return d


def init_db():
    engine = create_engine(BaseConfig.SQLALCHEMY_DATABASE_URI, convert_unicode=True)
    db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
    Base.query = db_session.query_property()
    Base.metadata.create_all(bind=engine)
    return db_session