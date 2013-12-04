from pprint import pformat
import urllib
import datetime
import logging

from zope.interface import implements
from twisted.internet import reactor, defer
from twisted.internet.defer import Deferred, succeed
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent
from twisted.web.http_headers import Headers
from twisted.web.iweb import IBodyProducer
import json

class BufferProtocol(Protocol):
	def __init__(self, finished):
		self.buffer = []
		self.finished = finished

	def dataReceived(self, data):
		self.buffer.append(data)

	def connectionLost(self, reason):
		
		print 'Finished receiving body:', reason.getErrorMessage()
		#Callback with the buffer contents
		self.finished.callback(''.join(self.buffer))
		#return ''.join(self.buffer)
		#return self.finished

class StringProducer(object):
	"""from: http://twistedmatrix.com/documents/12.2.0/web/howto/client.html
	a simple IBodyProducer implementation which writes an in-memory string to the consumer:

	"""
	implements(IBodyProducer)

	def __init__(self, body):
		self.body = ''
		if isinstance(body, str):
			self.body = body
		elif isinstance(body, list) or isinstance(body, dict):
			self.body = json.dumps(body)
			#print "stringifiy: %s" % 
		else:
			pass #print warning to log?
		self.length = len(self.body)

	def startProducing(self, consumer):
		consumer.write(self.body)
		return succeed(None)

	def pauseProducing(self):
		pass

	def stopProducing(self):
		pass




def agent_printer(response):
	print 'Response version:', response.version
	print 'Response code:', response.code
	print 'Response phrase:', response.phrase
	print 'Response headers:'
	print pformat(list(response.headers.getAllRawHeaders()))
	defer = Deferred()
	response.deliverBody(BufferProtocol(defer))
	return defer

#def _key_checker(func):
#	def inner(self, *args, **kwargs):
#		if func.__name__ in ['channel_status'] and self.key_read == None:
#			logging.warn('Cannot perform \'%s\' without setting key_read.' % func.__name__)
#			return None
#		if func.__name__ in ['channel_update'] and self.key_write == None:
#			logging.warn('Cannot perform \'%s\' without setting key_write.' % func.__name__)
#			return None
#		else:
#			return func(self, *args, **kwargs)
#	return inner



class ChannelClient(object):
	def __init__(self, url_domain=None, key_read=None, key_write=None, ssl=True, decode_json=True):
		self.url_domain = url_domain
		self.key_read = key_read
		self.key_write = key_write
		self.url = '%s://%s' % (('https' if ssl else 'http'), url_domain)
		self.decode_json = decode_json
		self.agent = Agent(reactor)

	def _decode_json(self, body):
		return json.loads(body)

	def _request(self, service, method='GET', **kwargs):
		param_dict = {}

		#Add 'key' to params_dict:
		if service.startswith('channel'):
			if self.key_read != None:
				param_dict['key'] = self.key_read
			else:
				logging.warn('Cannot perform \'%s\' without setting key_read.' % service)
				return defer.Deferred()
				#raise Exception('Missing Key')
		elif service.startswith('update'):
			if self.key_write != None:
				param_dict['key'] = self.key_write
			else:
				logging.warn('Cannot perform \'%s\' without setting key_write.' % service)
				return defer.fail()
				#raise Exception('Missing Key')
				#return defer.fail()


#			'key': self.key,
#		}
#		for pname, pvalue in kwargs.iteritems():
#			if pvalue != None:
#				param_dict[pname] = pvalue
		
		body_producer = None
		if method == 'POST':
			body_producer = StringProducer(urllib.urlencode(kwargs))
#		if value != None:
#			data_dict = {}
#			data_dict['d'] = value
#			if isinstance(date, str):
#				data_dict['t'] = date
#			elif isinstance(date, datetime.datetime):
#				#milliseconds epoch time
#				e = datetime.datetime.utcfromtimestamp(0)
#				data_dict['t'] = str(int((date - e).total_seconds() * 1000))
#			body_producer = StringProducer(data_dict)
#		elif values != None:
#			body_producer = StringProducer(values)
#		url = '%s/%s' % (self.url, '%s' % (service,))
		url = '%s/%s' % (self.url, '%s?%s' % (service, urllib.urlencode(param_dict),))
		logging.debug('%s %s' % (method, url))
		if body_producer:
			logging.debug('BODY:\n%s\n' % (body_producer.body,))
		request = self.agent.request(method=method,
			uri = url,
			bodyProducer = body_producer
		)
		return request

	def channel_update(self, **params):
		request = self._request('update', method='POST', **params)
		request.addCallback(agent_printer)
		if self.decode_json:
			request.addCallback(self._decode_json)
		return request

	def channel_feed(self, channel_id):
		request = self._request('channels/%s/feed.json' % (channel_id,))
		request.addCallback(agent_printer)
		if self.decode_json:
			request.addCallback(self._decode_json)
		return request

	def channel_feed_last(self, channel_id):
		request = self._request('channels/%s/feed/last.json' % (channel_id,))
		request.addCallback(agent_printer)
		if self.decode_json:
			request.addCallback(self._decode_json)
		return request

	def channel_feed_field(self, channel_id, field_id):
		request = self._request('channels/%s/field/%s.json' % (channel_id, field_id))
		request.addCallback(agent_printer)
		if self.decode_json:
			request.addCallback(self._decode_json)
		return request

	def channel_feed_field_last(self, channel_id, field_id):
		request = self._request('channels/%s/field/%s/last.json' % (channel_id, field_id))
		request.addCallback(agent_printer)
		if self.decode_json:
			request.addCallback(self._decode_json)
		return request

	def channel_status(self, channel_id):
		request = self._request('channels/%s/status.json' % (channel_id))
		request.addCallback(agent_printer)
		if self.decode_json:
			request.addCallback(self._decode_json)
		return request
		
