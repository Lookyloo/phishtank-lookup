#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pkg_resources
from typing import Dict

from flask import request, Flask
from flask_restx import Api, Namespace, Resource, fields  # type: ignore

from phishtank.phishtank import Phishtank

from .helpers import get_secret_key
from .proxied import ReverseProxied

api = Namespace('GenericAPI', description='Generic Phishtank API', path='/')

app: Flask = Flask(__name__)

app.wsgi_app = ReverseProxied(app.wsgi_app)  # type: ignore

app.config['SECRET_KEY'] = get_secret_key()

api = Api(app, title='Phishtank API',
          description='API to query a Phishtank lookup instance.',
          version=pkg_resources.get_distribution('phishtank').version)

phishtank: Phishtank = Phishtank()

checkurl_fields = api.model('CheckURLFields', {
    'url': fields.Url(description="The URL to check", required=True),
})


@api.route('/checkurl')
@api.doc(description='This method has the same JSON output as the (broken?) official interface.')
class CheckURL(Resource):

    def _format_response(self, url: str) -> Dict:
        entry = phishtank.get_url_entry(url)
        if not entry:
            return {'in_database': False}
        return {
            'url': url,
            'in_database': True,
            'phish_id': entry['phish_id'],
            'phish_detail_page': entry['phish_detail_url'],
            'verified': 'y',
            'verified_at': entry['verification_time'],
            'valid': 'y'
        }

    @api.param('url', 'The URL to check', required=True)
    def get(self):
        if 'url' not in request.args or not request.args.get('url'):
            return {'error': 'The URL is required...'}, 400
        return self._format_response(request.args['url'])

    @api.doc(body=checkurl_fields)
    def post(self):
        to_query: Dict = request.get_json(force=True)
        if 'url' not in to_query:
            return {'error': 'The URL is required...'}, 400
        return self._format_response(to_query['url'])


@api.route('/urls')
@api.doc(description='Get all the URLs')
class URLs(Resource):

    def get(self):
        return phishtank.get_urls()


@api.route('/ips')
@api.doc(description='Get all the IPs')
class IPs(Resource):

    def get(self):
        return phishtank.get_ips()


@api.route('/asns')
@api.doc(description='Get all the ASNs')
class ASNs(Resource):

    def get(self):
        return phishtank.get_asns()


@api.route('/ccs')
@api.doc(description='Get all the Country Codes')
class CCs(Resource):

    def get(self):
        return phishtank.get_ccs()


@api.route('/urls_by_ip')
@api.doc(description='Get all the URLs by IP')
class URLsByIPs(Resource):

    @api.param('ip', 'The IP to query', required=True)
    def get(self):
        if 'ip' not in request.args or not request.args.get('ip'):
            return {'error': 'The IP is required...'}, 400
        return phishtank.get_urls_by_ip(request.args['ip'])


@api.route('/urls_by_asn')
@api.doc(description='Get all the URLs by ASN')
class URLsByASN(Resource):

    @api.param('asn', 'The ASN to query', required=True)
    def get(self):
        if 'asn' not in request.args or not request.args.get('asn'):
            return {'error': 'The ASN is required...'}, 400
        return phishtank.get_urls_by_asn(request.args['asn'])


@api.route('/urls_by_cc')
@api.doc(description='Get all the URLs by Country Code')
class URLsByCC(Resource):

    @api.param('cc', 'The CC to query', required=True)
    def get(self):
        if 'cc' not in request.args or not request.args.get('cc'):
            return {'error': 'The Country Code is required...'}, 400
        return phishtank.get_urls_by_cc(request.args['cc'])
