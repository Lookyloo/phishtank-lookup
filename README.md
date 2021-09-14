# phishtank-lookup
Simple web API using the hourly dump from Phishtank

This tool loads the [public dump](https://phishtank.org/developer_info.php) from [Phishtank](https://phishtank.org/), 
loads it into Redis and allows to run queries against it. Note that it only contains the online and valid entries and is updated once per hour.
