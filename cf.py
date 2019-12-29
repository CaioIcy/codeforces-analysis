#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
from scipy.stats import spearmanr


def req(api_method, renew=False):
    try:
        if renew:
            raise
        with open(f'./cache/{api_method}.json', 'r') as cache:
            return json.loads(cache.read())
    except:
        import requests
        response = requests.get(f'https://codeforces.com/api/{api_method}')
        with open(f'./cache/{api_method}.json', 'w') as cache:
            cache.write(response.text)
        return json.loads(response.text)


def get_rated_users(active):
    return req(f'user.ratedList?activeOnly={"true" if active else "false"}')


def get_user_rating_changes(handle):
    return req(f'user.rating?handle={handle}')


def bucket_key(rating):
    for bucket in [2600,2400,2200,2100,2050,2000,1950,1900]:
        if rating >= bucket:
            return bucket
    return 0


def num_contests_to(rating_changes, to_rating):
    num_contests = 0
    for r in rating_changes:
        if r['oldRating'] >= to_rating:
            break
        num_contests += 1
    return num_contests

us = get_rated_users(False)
# us = get_rated_users(True)

min_max_rating = 1900

df = pd.DataFrame(us["result"], columns=['handle', 'maxRating', 'rating'])
df = df[df.maxRating >= min_max_rating]
# df = df.sample(frac=0.05)
df = df.nlargest(len(df), 'maxRating')

i = 0
x_vals = []
y_vals = []
buckets = defaultdict(list)

for df_idx in range(0, len(df)):
    curr = df.iloc[df_idx]
    h = curr.handle
    mx = curr.maxRating

    print(f'[{i}={h}={mx}] ', end='')
    rc = get_user_rating_changes(h)
    if rc["status"] != "OK":
        continue

    res = rc["result"]
    if len(res) < 3:
        i += 1
        continue

    value = num_contests_to(res, min_max_rating)
    buckets[bucket_key(mx)].append(value)
    x_vals.append(mx)
    y_vals.append(value)
    i += 1
########################

sorted_bucket_keys = sorted(buckets.keys())
print(sorted_bucket_keys)

plot_scatter = False

fig, ax = plt.subplots(figsize=(640/80., 320/80.), dpi=80)
ax.set(xlabel='maxRating' if plot_scatter else 'maxRating buckets', ylabel=f'#contests to achieve rating {min_max_rating}',
title='')
ax.grid()

if plot_scatter:
    ax.scatter(x_vals, y_vals, c=y_vals, cmap='tab20')
else:
    percentiles = [25,50,75,90]
    for p in percentiles:
        xx = []
        yy = []
        for k in sorted_bucket_keys:
            v = buckets[k]
            xx.append(k)
            yy.append(np.percentile(v, p))
        ax.plot(xx, yy, 'o:', label=f'{p}th ptl')

    xx = []
    yy = []
    for k in sorted_bucket_keys:
        v = buckets[k]
        print(f'{k} rt N={len(v)}')
        xx.append(k)
        yy.append(np.mean(v))
    ax.plot(xx, yy, '-', label='mean')

    ax.legend()

print(f'pd.corr spearman = {pd.Series(x_vals).corr(pd.Series(y_vals), "spearman")}')
print(spearmanr(x_vals, y_vals))
plt.show()
