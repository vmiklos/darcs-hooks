#!/usr/bin/env python

import os, gzip, re, xmlrpclib
from xml.sax import saxutils
from xml.dom import minidom
from config import config

__version__ = "0.1.0"
__url__ = "http://ftp.frugalware.org/pub/other/darcs-hooks"

def getpatch(hash):
	sock = gzip.GzipFile(os.path.join("_darcs", "patches", "%s") % hash)
	data = sock.readlines()
	sock.close()
	return data

def tobuild(pkg):
	ret = []
	# Build the command to read the FrugalBuilds
	command = 'source /usr/lib/frugalware/fwmakepkg'
	command += ' ; source %s'
	command += ' ; [ -n "${nobuild}" ] && exit'
	command += ' ; echo ${options[@]} | grep -q nobuild && exit'
	command += ' ; echo "${pkgname}-${pkgver}-${pkgrel}"'
	command += ' ; echo "${archs[@]}"'
	sock = os.popen(command % pkg)
	lines = sock.readlines()
	sock.close()
	if not len(lines):
		return ret
	archs = lines[1].strip().split()
	for i in archs:
		if i not in config.archs:
			continue
		full = "-".join([lines[0].strip(), i])
		try:
			os.stat("frugalware-%s/%s.fpm" % (i, full))
		except OSError:
			ret.append(full)
	return ret

def callback(patch):
	global config
	files = []
	repo = os.path.split(os.getcwd())[-1]
	if repo not in config.repos:
		print "repos is '%s', exiting" % repo
		return
	hash = saxutils.unescape(patch.attributes['hash'].firstChild.toxml())
	patchdata = getpatch(hash)
	server = xmlrpclib.Server(config.server_url)
	pkgs = []
	for i in patchdata:
		i = i.strip().replace("./", "")
		if i.startswith("hunk "):
			file = re.sub(r"^hunk (.*) [0-9]+", r"\1", i)
			if re.match("^source/[^/]+/[^/]+/FrugalBuild$", file):
				for j in tobuild(file):
					# hardwiring this is ugly
					pkg = "darcs://%s/%s" % (repo.replace("frugalware-0.6", "stable"), j)
					if pkg not in pkgs:
						pkgs.append(pkg)
	for i in pkgs:
		#server.request_build(config.server_user, config.server_pass, i)
		pass

if __name__ == "__main__":
	def getxml(cmd):
		sock = os.popen(cmd)
		xmldata = "".join(sock.readlines())
		sock.close()
		xmldoc = minidom.parseString(xmldata)
		return xmldoc

	os.chdir("/home/vmiklos/darcs/terminus")
	xmldoc = getxml("darcs chan --last 1 --xml-output")
	patch = xmldoc.getElementsByTagName('patch')[0]
	callback(patch)
