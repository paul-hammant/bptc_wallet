import threading
from twisted.internet import reactor, threads

from bptc.utils import logger
from .push_protocol import PushServerFactory
from .query_members_protocol import QueryMembersClientFactory
from .register_protocol import RegisterClientFactory
from .pull_protocol import PullServerFactory

def start_reactor_thread():
    def start_reactor():
        reactor.run(installSignalHandlers=0)
    threading.Thread(target=start_reactor).start()

def stop_reactor_thread():
    reactor.callFromThread(reactor.stop)

def register(member_id, listening_port, registry_ip, registry_port):
    factory = RegisterClientFactory(str(member_id), int(listening_port))
    def register():
        reactor.connectTCP(registry_ip, int(registry_port), factory)
    threads.blockingCallFromThread(reactor, register)

def process_query(client, members):
    new_members = {}
    print(client, members)
    for member_id, (ip, port) in members.items():
        if member_id != str(client.me.id):
            new_members[member_id] = (ip, port)
            # self.neighbours[member_id] = (ip, port)
    logger.info("Acquainted with {}".format(new_members))

def query_members(client, query_members_ip, query_members_port):
    factory = QueryMembersClientFactory(client, lambda x: process_query(client, x))
    def query():
        reactor.connectTCP(query_members_ip, int(query_members_port), factory)
    threads.blockingCallFromThread(reactor, query)

def start_listening(network, listening_port):
    logger.info("Push server listens on port {}".format(listening_port))
    push_server_factory = PushServerFactory(network.receive_events_callback)
    reactor.listenTCP(int(listening_port), push_server_factory)

    logger.info("[Pull server (for viz tool) listens on port {}]".format(int(listening_port) + 1))
    pull_server_factory = PullServerFactory(network)
    reactor.listenTCP(int(listening_port) + 1, pull_server_factory)
