"""Elements for a tool to diagnose repositories"""

import pandas as pd
import requests
from io import BytesIO
import re
from typing import Union, Iterable

Url = str
Urls = Iterable[Url]
Table = Union[pd.DataFrame, Url, Urls]

github_url_p = re.compile(r'https?://github.com/(?P<org>[^/]+)/(?P<repo>[^/]+).*?')

# TODO: Make the following particulars controllable from outside module
DFLT_URL_TABLE_SOURCE = (
    'https://raw.githubusercontent.com/otosense/content/main/tables/projects.csv'
)
docs_url_template = 'https://{org}.github.io/{repo}'
repo_docs_url_template = 'https://github.com/{org}/{repo}/tree/master/docs'


def get_doc_state_for_oto_repos(df: Table = DFLT_URL_TABLE_SOURCE, url_column='url'):
    df = _get_table(df)
    df['doc_page_url'] = df[url_column].apply(repo_url_to_docs_url)
    df['doc_page_exists'] = df['doc_page_url'].apply(url_exists)
    df['repo_has_docs_folder'] = df[url_column].apply(
        lambda url: url_exists(repo_url_to_repo_docs_url(url))
    )
    return df


def _get_table(df):
    if isinstance(df, str):
        url = df
        df = table_url_to_df(url)
    elif not isinstance(df, pd.DataFrame) and isinstance(df, Iterable):
        urls = df
        df = pd.DataFrame({'url': urls})
    return df


def github_org_and_repo(github_url):
    """
    >>> github_org_and_repo('https://github.com/i2mint/i2')
    {'org': 'i2mint', 'repo': 'i2'}
    """
    return github_url_p.match(github_url.strip()).groupdict()


def repo_url_to_docs_url(repo_url):
    """
    >>> repo_url_to_docs_url('https://github.com/i2mint/i2')
    'https://i2mint.github.io/i2'
    """
    return docs_url_template.format(**github_org_and_repo(repo_url))


def repo_url_to_repo_docs_url(repo_url):
    """
    >>> repo_url_to_repo_docs_url('https://github.com/i2mint/i2')
    'https://github.com/i2mint/i2/tree/master/docs'
    """
    return repo_docs_url_template.format(**github_org_and_repo(repo_url))


def table_url_to_df(url: Url):
    html = requests.get(url).content
    df = pd.read_csv(BytesIO(html))
    df.columns = [column_name.strip() for column_name in df.columns]
    return df


def is_valid_response(response):
    return response.status_code == 200


def url_exists(url):
    return is_valid_response(requests.get(url))
