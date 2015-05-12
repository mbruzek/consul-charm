# Consul

Consul is a tool for discovering and configuring services.

**Key Features**:

* **Service Discovery**: Clients of Consul can *provide* a service, while other
clients can use Consul to *discover* providers of a given service.  The service
discovery can be accessed via DNS or HTTP so applications can easily find the
services they depend upon.
* **Health Checking**: Consul clients can provide any number of health checks,
either associated with a given service, or with the local node. This information
can be used to monitor cluster heath and is used by service discovery components
to route traffic away from unhealthy hosts.
* **Key/Value Store**: Applications can use Consul's hierarchical key/value
store for any number of purposes, including dynamic configuration, feature
flagging, coordination, leader election, and more.  The simple HTTP API makes
the key/value store easy to use.
* **Multi Datacenter**: Consul supports multiple datacenters out of the box.
Consul grows to multiple regions.

# Usage

The Consul charm can be deployed from the command line:

    juju deploy consul

To be highly available deploy multiple units of the consul charm. The number of
units in the cluster should be odd and the
[Consul documentation](https://www.consul.io/docs/agent/options.html)
suggests no more than 5 per datacenter.

    juju deploy -n 3 consul


### Ports Used

Consul requires up to 5 different ports to work properly, some on TCP, UDP, or
both protocols. Below we document the requirements for each port.

- Server RPC (Default 8300). This is used by servers to handle incoming requests
 from other agents. TCP only.

- Serf LAN (Default 8301). This is used to handle gossip in the LAN. Required by
 all agents. TCP and UDP.

- Serf WAN (Default 8302). This is used by servers to gossip over the WAN to
other servers. TCP and UDP.

- CLI RPC (Default 8400). This is used by all agents to handle RPC from the CLI.
TCP only.

- HTTP API (Default 8500). This is used by clients to talk to the HTTP API. TCP
only.

- DNS Interface (Default 8600). Used to resolve DNS queries. TCP and UDP.


## Scale out Usage

Each Consul cluster must have at least one server and ideally no more than 5
per datacenter. All servers participate in the Raft consensus algorithm to
ensure that transactions occur in a consistent, linearizable manner.
Transactions modify cluster state, which is maintained on all server nodes to
ensure availability in the case of node failure. Server nodes also participate
in a WAN gossip pool with server nodes in other datacenters. Servers act as
gateways to other datacenters and forward traffic as appropriate.

# Configuration

The Consul software has only a few
[reloadable configuration](https://www.consul.io/docs/agent/options.html#reloadable-configuration)
options.  

This charm exposes the following configuration values:  

**log-level** - The level of logging to show after the Consul agent has started.
This defaults to "info". The available log levels are "trace", "debug", "info",
"warn", and "err". Note that you can always connect to an agent via consul
monitor and use any log level.

**domain** - By default, Consul responds to DNS queries in the "consul." domain.
This flag can be used to change that domain. All queries in this domain are
assumed to be handled by Consul and will not be recursively resolved.

## Contact Information

The original author of this charm is Kapil Thangavelu ( @kapilt ).  

The Consul charm maintainers are:
- Charles Butler ( @chuckbutler )  
- Matthew Bruzek ( @mbruzek )  
- Whit Morriss ( @whitmo )  

# Consul Information

- [Consul website](https://www.consul.io)
- [Consul documentation](https://www.consul.io/docs/index.html)
- [Consul github](https://github.com/hashicorp/consul)
- Bug Tracker: [Issue tracker on GitHub](https://github.com/hashicorp/consul/issues)
Use to report bugs, ask for general help in the IRC or mailing list.
- Mailing list: [Consul Google Group](https://groups.google.com/forum/#!forum/consul-tool)
- IRC: `#consul` on Freenode
- Community tools: [Download Consul tools](https://www.consul.io/downloads_tools.html)
Please check out some of the awesome Consul tooling our amazing community has
helped build.
