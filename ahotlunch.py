import html5lib
import requests
from absl import logging
from configobj import ConfigObj

import json
import os

# a lot borrowed from https://github.com/google/github_nonpublic_api.  Which means that maybe some of that should live in it's own library?


def _get_form(session, url: str):
    logging.info("Fetching URL %s", url)
    response = session.get(url)
    response.raise_for_status()
    return response


def _submit_form(
    session, url: str, text: str, data_callback=None, form_matcher=lambda form: True
):
    doc = html5lib.parse(text, namespaceHTMLElements=False)
    forms = doc.findall(".//form")

    submit_form = None
    for form in forms:
        if form_matcher(form):
            submit_form = form
            break
    if submit_form is None:
        raise ValueError("Unable to find form")

    action_url = submit_form.attrib["action"]
    # Look at all the inputs under the given form.
    inputs = submit_form.findall(".//input")

    data = dict()
    for form_input in inputs:
        value = form_input.attrib.get("value")
        if value and "name" in form_input.attrib:
            data[form_input.attrib["name"]] = value

    # Have the caller provide additional data
    if data_callback:
        data_callback(data)

    logging.debug("Form data: %s", str(data))

    submit_url = urljoin(url, action_url)
    logging.info("Posting form to URL %s", submit_url)

    response = session.post(submit_url, data=data)
    response.raise_for_status()
    return response


def _get_and_submit_form(
    session, url: str, data_callback=None, form_matcher=lambda form: True
):
    response = _get_form(session=session, url=url)
    return _submit_form(
        session=session,
        url=url,
        text=response.text,
        data_callback=data_callback,
        form_matcher=form_matcher,
    )


def _get_url_with_session(session, url: str):
    logging.info("Fetching URL %s", url)
    response = session.get(url)
    response.raise_for_status()
    return response


def create_login_session(
    username: str, password: str, session: requests.Session = None
) -> requests.Session:
    """Create a requests.Session object with logged in GitHub cookies for the user."""

    session = session or requests.Session()
    resp = session.post('https://mygreenlunch.ahotlunch.com/login/check', dict(login=username, password=password))
    return session


_CALENDAR_URL = "https://mygreenlunch.ahotlunch.com/order/cGet?endDate=%s&startDate=%s&typeId="

def get_calendar(s, start_date, end_date):
    resp = s.get(_CALENDAR_URL % (end_date, start_date))
    resp.raise_for_status()
    data = json.loads(resp.content)
    if data.get('status') != 'success':
        raise ValueError(data.get('status'))
    return data.get('data')

def main():
    config = ConfigObj(os.path.expanduser("~/ahotlunch.ini"), _inspec=True)

    s = create_login_session(
        username=config.get("username"), password=config.get("password")
    )
    
    data = get_calendar(s, '2023-09-01', '2023-12-31')
    for item in data.values():
        item = item[0]
        print(item.get('name'), item.get('orderDate'))



if __name__ == "__main__":
    logging.set_verbosity(1)
    main()
