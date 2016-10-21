"""Look up vulnerabilities in the CVE database."""

import re
import urllib.parse

from plumeria.command import commands, CommandError
from plumeria.util import http
from plumeria.util.ratelimit import rate_limit

CVE_PATTERN = re.compile("^(CVE-\\d{4,5}-\d+)$", re.IGNORECASE)


@commands.create("cve", category="Search")
@rate_limit()
async def cve(message):
    """
    Look up information about a CVE.

    Example::

        /cve CVE-2010-3213

    Response::

        CVE-2010-3213 - Cross-site request forgery (CSRF) vulner[...]
        Auth: NONE / Complexity: MEDIUM / Vector: NETWORK
        https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2010-3213
        • (462) Cross-Domain Search Timing
        • (467) Cross Site Identification
        • (62) Cross Site Request Forgery (aka Session Riding)
        • (111) JSON Hijacking (aka JavaScript Hijacking)

    """
    q = message.content.strip()
    if not q:
        raise CommandError("Search term required!")
    m = CVE_PATTERN.search(q)
    if not m:
        raise CommandError("No CVE found in the given input")
    r = await http.get("https://cve.circl.lu/api/cve/{}".format(m.group(1).upper()))
    data = r.json()
    if len(data.keys()):
        capecs = "\n".join(
            map(lambda e: "\u2022 ({id}) {name}".format(id=e['id'], name=e['name']), data.get("capec", [])))
        return "**{cve}** [{cvss}] - {summary}\n*Auth: {auth} / Complexity: {complexity} / Vector: {vector}*\n<{url}>\n{capecs}".format(
            cve=data['id'],
            cvss=data['cvss'],
            summary=data['summary'],
            auth=data['access']['authentication'],
            complexity=data['access']['complexity'],
            vector=data['access']['vector'],
            capecs=capecs,
            url="https://cve.mitre.org/cgi-bin/cvename.cgi?name={}".format(urllib.parse.quote(data['id'])))
    else:
        raise CommandError("no results found")


def setup():
    commands.add(cve)
