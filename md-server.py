import sys
import os
import logging

import bottle
from bottle import route, run, template

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)
LOG.addHandler(logging.StreamHandler())

USERDATA_TEMPLATE = """\
#cloud-config
hostname: {{hostname}}
password: {{password}}
chpasswd: { expire: False }
ssh_pwauth: True
ssh_authorized_keys:
    - {{public_key_default}}
"""


class MetadataHandler(object):

    def gen_metadata(self):
        res = ["instance-id",
               "hostname",
               "public-keys",
               ""]
        return self.make_content(res)

    def gen_userdata(self):
        config = bottle.request.app.config
        config['public_key_default'] = config['public-keys.default']
        config['hostname'] = self.gen_hostname().strip('\n')
        user_data = template(USERDATA_TEMPLATE, **config)
        return self.make_content(user_data)

    def gen_hostname(self):
        client_host = bottle.request.get('REMOTE_ADDR')
        prefix = bottle.request.app.config['hostname-prefix']
        res = "%s-%s" % (prefix, client_host.split('.')[-1])
        return self.make_content(res)

    def gen_public_keys(self):
        res = bottle.request.app.config.keys()
        _keys = filter(lambda x: x.startswith('public-keys'), res)
        keys = map(lambda x: x.split('.')[1], _keys)
        keys.append("")
        return self.make_content(keys)

    def gen_public_key_dir(self, key):
        res = ""
        if key in self.gen_public_keys():
            res = "openssh-key"
        return self.make_content(res)

    def gen_public_key_file(self, key='default'):
        if key not in self.gen_public_keys():
            key = 'default'
        res = bottle.request.app.config['public-keys.%s' % key]
        return self.make_content(res)

    def gen_instance_id(self):
        client_host = bottle.request.get('REMOTE_ADDR')
        iid = "i-%s" % client_host
        return self.make_content(iid)

    def make_content(self, res):
        if isinstance(res, list):
            return "\n".join(res)
        elif isinstance(res, basestring):
            return "%s\n" % res


def main():
    app = bottle.default_app()
    app.config['md-base'] = "/2009-04-04"
    app.config['password'] = "password"
    app.config['hostname-prefix'] = 'vm'
    app.config['public-keys.default'] = "__NOT_CONFIGURED__"

    if len(sys.argv) > 1:
        config_file = sys.argv[1]
        if os.path.exists(config_file):
            app.config.load_config(config_file)

    if app.config['public-keys.default'] == "__NOT_CONFIGURED__":
        LOG.info("================Default public key not set !!!==============")

    mdh = MetadataHandler()
    route(app.config['md-base'] + '/meta-data/',
          'GET', mdh.gen_metadata)
    route(app.config['md-base'] + '/user-data',
          'GET', mdh.gen_userdata)
    route(app.config['md-base'] + '/meta-data/hostname',
          'GET', mdh.gen_hostname)
    route(app.config['md-base'] + '/meta-data/instance-id',
          'GET', mdh.gen_instance_id)
    route(app.config['md-base'] + '/meta-data/public-keys',
          'GET', mdh.gen_public_keys)
    route(app.config['md-base'] + '/meta-data/public-keys/',
          'GET', mdh.gen_public_keys)
    route(app.config['md-base'] + '/meta-data/<key>',
          'GET', mdh.gen_public_key_dir)
    route(app.config['md-base'] + '/meta-data/<key>/',
          'GET', mdh.gen_public_key_dir)
    route(app.config['md-base'] + '/meta-data/<key>/openssh-key',
          'GET', mdh.gen_public_key_file)
    route(app.config['md-base'] + '/meta-data//<key>/openssh-key',
          'GET', mdh.gen_public_key_file)
    route(app.config['md-base'] + '/meta-data/public-keys//<key>/openssh-key',
          'GET', mdh.gen_public_key_file)
    route('/latest' + '/meta-data/public-keys//<key>/openssh-key',
          'GET', mdh.gen_public_key_file)
    run(host='169.254.169.254', port=80)

if __name__ == '__main__':
    main()
