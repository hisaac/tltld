#!/usr/bin/env python

import requests
import socket
import timeit
from collections import defaultdict
from queue import Queue
from threading import Thread


total_tlds = 0
checked_so_far = 0
domain_availability = defaultdict(bool)


def print_percent_done(bar_len=50, title='Checking Domains'):
    global total_tlds
    global checked_so_far
    checked_so_far += 1

    percent_done = checked_so_far / total_tlds * 100
    percent_done = round(percent_done, 1)

    done = round(percent_done / (100 / bar_len))
    togo = bar_len - done

    done_str = '█' * int(done)
    togo_str = '░' * int(togo)

    if percent_done < 100:
        print(f'{title}: [{done_str}{togo_str}] {percent_done}%', end='\r')
    elif percent_done == 100:
        print(f'{title}: [{done_str}{togo_str}] {percent_done}%', end='\n\n')


def get_tld_list():
    tld_list_url = "https://data.iana.org/TLD/tlds-alpha-by-domain.txt"

    try:
        tld_list_raw = requests.get(tld_list_url)
    except requests.RequestException as exception:
        print(exception)
        raise exception

    tld_list_split = tld_list_raw.text.lower().splitlines()
    global total_tlds
    total_tlds = len(tld_list_split)

    tld_list_no_comments = list(filter(comments_filter, tld_list_split))
    return tld_list_no_comments


def comments_filter(line):
    return not line.startswith("#")


def check_tlds(queue):
    global domain_availability
    for domain in iter(queue.get, None):
        try:
            socket.getaddrinfo(domain, 0)
        except socket.gaierror:
            domain_availability[domain] = True
        else:
            domain_availability[domain] = False
        finally:
            print_percent_done()


def check_domain(domain):
    tld_list = get_tld_list()
    global total_tlds
    total_tlds = len(tld_list)

    # Spawn thread pool
    queue = Queue()
    threads = [Thread(target=check_tlds, args=(queue,)) for _ in range(20)]
    for thread in threads:
        thread.daemon = True
        thread.start()

    # Place work in queue
    for tld in tld_list:
        full_domain = domain + "." + tld
        queue.put(full_domain)

    # Put sentinel to signal the end
    for _ in threads:
        queue.put(None)

    # Wait for completion
    for thread in threads:
        thread.join()

    global domain_availability
    for domain in sorted(sorted(domain_availability), key=len):
        if domain_availability[domain]:
            print("✅  " + domain)
        else:
            print("❌  " + domain)


start = timeit.default_timer()
check_domain("ike")
print("\nExecution time: ", timeit.default_timer() - start)
