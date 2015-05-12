Introduction
------------

Consul provides several core features

  - Service Discovery via dns or http
  - Health Checking (interops with nagios)
  - Key/Value Store
  - Multiple data center support


Usage
-----

 The Consul charm exposes a few high level configuration options.

 Consul can be deployed via the cli with:

 $ juju deploy -n 3 cs:~hazmat/trusty/consul

 Note consul requires multiple units at the moment before it will
 establish itself as operational in order to ensure a quorum.

 After consul is deployed we can either use it directly with
 consul-agent or a the container-discovery subordinate charms.

 The consul agent requires explicit service configuration.

 The container discovery automates the registration of docker containers
 into the discovery system.


Todo
----

 - convert consul.json to directory to allow for dropping in watch checks
   and health

 - support tls/ssl for client api protocol

Authors
-------

Kapil Thangavelu ( @kapilt )
