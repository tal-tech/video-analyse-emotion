import logging
import os


def env_int(key):
    return int(os.environ.get(key)) if os.environ.get(key) else None


class Config:
    API_TYPE = os.environ.get('API_TYPE') or '1'
    EUREKA_HOST_NAME = os.environ.get('EUREKA_HOST_NAME') or 'video-analyse-emotion'
    EUREKA_APP_NAME = os.environ.get('EUREKA_APP_NAME') or 'VIDEO-ANALYSE-EMOTION'
    APOLLO_ID = os.environ.get('APOLLO_ID') or ''
    APOLLO_NAMESPACE = os.environ.get('APOLLO_NAMESPACE') or 'datawork-common'
    APP_URL = os.environ.get('APP_URL') or '/aivideo/video-analysis/emotion'
    APOLLO_TOPIC = os.environ.get('APOLLO_TOPIC') or 'image'
    BIZ_TYPE = os.environ.get('BIZ_TYPE') or 'datawork-image'

    BASE_FOLDER = os.path.dirname(os.path.abspath(__file__))
    TMP_FOLDER = os.path.join(BASE_FOLDER, 'temp')
    if not os.path.exists(TMP_FOLDER):
        os.mkdir(TMP_FOLDER)
    PORT = 5000
    REDIS_QUEUE = "video-analyse-emotion-v13"
    REDIS_EXPIRE = 3 * 24 * 60 * 60
    REDIS_PW = os.environ.get("REDIS_HOST") or 'ib2nH4XAB!%PK*Ca'
    REDIS_HOST = os.environ.get("REDIS_HOST") or 'r-2zeadx5rzfworu9w62.redis.rds.aliyuncs.com'
    REDIS_DB = os.environ.get("REDIS_DB") or 0
    REDIS_PORT = env_int("REDIS_PORT") or 6379

    POOL_PROCESS = env_int('POOL_PROCESS') or 3

    DEPLOY_ENV = os.environ.get('DEPLOY_ENV') or 'local'
    if DEPLOY_ENV == 'local':
        EUREKA_URL = 'http://AILab:PaaS@eureka-dev.facethink.com/eureka/'
        APOLLO_URL = 'http://godhand-apollo-config:8080'
        DATA_CHANGE_URL = 'http://internal.gateway-godeye-test.facethink.com/ossurl/material/ossconverts'
    elif DEPLOY_ENV == "test":
        EUREKA_URL = 'http://AILab:PaaS@godhand-eureka:8761/eureka/'
        APOLLO_URL = 'http://godhand-apollo-config:8080'
        DATA_CHANGE_URL = 'http://internal.gateway-godeye-test.facethink.com/ossurl/material/ossconverts'
    elif DEPLOY_ENV == "pre":
        EUREKA_URL = 'http://AILab:PaaS@godhand-eureka-master:8761/eureka/,http://AILab:PaaS@godhand-eureka-slave1:8761/eureka/,http://AILab:PaaS@godhand-eureka-slave2:8761/eureka/'
        APOLLO_URL = 'http://godhand-apollo-config:8080'
        DATA_CHANGE_URL = 'http://internal.gateway.facethink.com/ossurl/material/ossconverts'
    elif DEPLOY_ENV == 'prod':
        EUREKA_URL = 'http://AILab:PaaS@godhand-eureka-master:8761/eureka/,http://AILab:PaaS@godhand-eureka-slave1:8761/eureka/,http://AILab:PaaS@godhand-eureka-slave2:8761/eureka/'
        APOLLO_URL = 'http://godhand-apollo-config:8080'
        DATA_CHANGE_URL = 'http://internal.openai.100tal.com/ossurl/material/ossconverts'

    if os.environ.get('EUREKA_URL'):
        EUREKA_URL = os.environ.get('EUREKA_URL')
    if os.environ.get('APOLLO_URL'):
        APOLLO_URL = os.environ.get('APOLLO_URL')

    APOLLO_KAFKA = os.environ.get('APOLLO_KAFKA') or 'kafka-bootstrap-servers'
    VERSION = os.environ.get('VERSION') or '1.3'

    if os.environ.get('LOG_LEVEL') == 'DEBUG':
        LOG_LEVEL = logging.DEBUG
    elif os.environ.get('LOG_LEVEL') == 'INFO':
        LOG_LEVEL = logging.INFO
    else:
        LOG_LEVEL = logging.DEBUG

