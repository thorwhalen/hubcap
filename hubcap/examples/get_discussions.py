"""Discussions acquisition 

Usage
*****

.. code-block:: console

    $ python -u scripts/dump_discussion.py --token $(gh auth token) --owner $(git remote get-url upstream | sed -e 's/.*github.com\///g' | sed -e 's/\/.*//g') --repository $(git remote get-url upstream | sed -e 's/\/$//g' -e 's/.*\///g') --discussion-number 1406 | tee 1406.json
"""

import json
import os

from config2py import simple_config_getter, get_app_data_folder
from dol import Files, wrap_kvs, TextFiles, path_get
import dill
import requests

LocalDillStore = wrap_kvs(Files, data_of_obj=dill.dumps, obj_of_data=dill.loads)
LocalJsonStore = wrap_kvs(TextFiles, data_of_obj=json.dumps, obj_of_data=json.loads)

APP_NAME = 'hubcap'
get_config = simple_config_getter(APP_NAME)
data_folder = os.path.join(get_app_data_folder(APP_NAME), 'data')
if not os.path.exists(data_folder):
    os.makedirs(data_folder)
from dol import path_get
from functools import partial

get_value = partial(path_get, get_value=lambda d, k: d.get(k, {}))


def get_discussion_numbers(repo, token=None):
    token = token or get_config('GITHUB_TOKEN')
    owner, repository = repo.split('/')
    headers = {'Authorization': f'Bearer {token}'}
    url = 'https://api.github.com/graphql'
    query = f'''
    query {{
      repository(owner: "{owner}", name: "{repository}") {{
        discussions(first: 150) {{
          nodes {{
            number
          }}
        }}
      }}
    }}
    '''
    response = requests.post(url, headers=headers, json={'query': query})
    response.raise_for_status()
    data = response.json()
    if errors := data.get('errors'):
        msg = '\n'.join([e['message'] for e in errors])
        raise RuntimeError(msg)
    return [
        node['number'] for node in get_value(data, 'data.repository.discussions.nodes')
    ]


async def discussion_data(repo, discussion_number, token=None):
    token = token or get_config('GITHUB_TOKEN')
    owner, repository = repo.split('/')
    async with aiohttp.ClientSession(trust_env=True) as session:
        discussion_data = await fetch_discussion_data(
            session, token, owner, repository, discussion_number
        )
    return discussion_data


async def download_and_save_discussion_data(
    repo, discussion_number, *, token=None, store=data_folder
):
    owner, repository = repo.split('/')
    if isinstance(discussion_number, int):
        discussion_number_str = f'{discussion_number:03.0f}'
    else:
        discussion_number_str = discussion_number
    save_filename = f'{owner}__{repository}__{discussion_number_str}.json'
    d = await discussion_data(f'{owner}/{repository}', discussion_number, token)
    if d is not None:
        if isinstance(store, str):
            rootdir = store
            store = LocalJsonStore(rootdir)
        store[save_filename] = d
    return d


import os
import asyncio
import aiohttp
import json
from dataclasses import dataclass
from typing import List
import argparse


@dataclass
class Reply:
    body: str


@dataclass
class Comment:
    body: str
    replies: List[Reply]


@dataclass
class Discussion:
    body: str
    title: str
    comments: List[Comment]


LocalDiscussionsStore = wrap_kvs(
    LocalJsonStore,
    obj_of_data=lambda d: Discussion(
        body=d['body'], title=d['title'], comments=d['comments']
    ),
)


async def fetch_discussion_data(session, token, owner, repository, discussion_number):
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

    query = '''
    query($owner: String!, $repository: String!, $discussionNumber: Int!, $commentsCursor: String, $repliesCursor: String) {
      repository(owner: $owner, name: $repository) {
        discussion(number: $discussionNumber) {
          title
          body
          comments(first: 100, after: $commentsCursor) {
            pageInfo {
              hasNextPage
              endCursor
            }
            nodes {
              body
              replies(first: 100, after: $repliesCursor) {
                pageInfo {
                  hasNextPage
                  endCursor
                }
                nodes {
                  body
                }
              }
            }
          }
        }
      }
    }

    '''

    # overwritting Discussion, Comment, Reply to dict to make json serializable
    Discussion = dict
    Comment = dict
    Reply = dict

    variables = {
        'owner': owner,
        'repository': repository,
        'discussionNumber': discussion_number,
    }

    discussion_data = []
    has_next_page = True
    comments_cursor = None

    while has_next_page:
        variables['commentsCursor'] = comments_cursor
        response = await session.post(
            'https://api.github.com/graphql',
            headers=headers,
            json={'query': query, 'variables': variables},
        )
        result = await response.json()

        # print(f"{result=}")

        discussion = result.get('data', {}).get('repository', {}).get('discussion', {})
        if discussion is None:
            return None

        discussion_title = discussion['title']
        discussion_body = discussion['body']
        comments = discussion['comments']['nodes']
        has_next_page = discussion['comments']['pageInfo']['hasNextPage']
        comments_cursor = discussion['comments']['pageInfo']['endCursor']

        for comment in comments:
            comment_body = comment['body']
            replies = []

            has_next_reply_page = True
            replies_cursor = None

            while has_next_reply_page:
                variables['repliesCursor'] = replies_cursor
                response = await session.post(
                    'https://api.github.com/graphql',
                    headers=headers,
                    json={'query': query, 'variables': variables},
                )
                reply_result = await response.json()

                reply_nodes = comment['replies']['nodes']
                has_next_reply_page = comment['replies']['pageInfo']['hasNextPage']
                replies_cursor = comment['replies']['pageInfo']['endCursor']

                for reply in reply_nodes:
                    replies.append(Reply(body=reply['body']))

            discussion_data.append(Comment(body=comment_body, replies=replies))

    return Discussion(
        title=discussion_title, body=discussion_body, comments=discussion_data
    )


async def main():
    parser = argparse.ArgumentParser(description='Fetch GitHub discussion data')
    parser.add_argument('--token', help='GitHub Access Token')
    parser.add_argument('--owner', help='GitHub Repository Owner')
    parser.add_argument('--repository', help='GitHub Repository Name')
    parser.add_argument(
        '--discussion-number', type=int, help='GitHub Discussion Number'
    )
    args = parser.parse_args()

    await download_and_save_discussion_data(
        args.owner, args.repository, args.discussion_number, args.token
    )
    # async with aiohttp.ClientSession(trust_env=True) as session:
    #     discussion_data = await fetch_discussion_data(
    #         session, args.token, args.owner, args.repository, args.discussion_number
    #     )
    #     print(json.dumps(discussion_data, default=lambda x: x.__dict__, indent=2))


if __name__ == '__main__':
    asyncio.run(main())
    # from argh import dispatch_command
    # dispatch_command(download_and_save_discussion_data)
