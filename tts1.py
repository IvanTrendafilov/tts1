import time
import re
import urllib2
import robotparser
import hashlib
import heapq

class Crawler(object):
	def __init__ (self, frontier):
		self.frontier = frontier
		self.followed = []
		self.rp = robotparser.RobotFileParser()	
		self.rp.set_url("http://ir.inf.ed.ac.uk/robots.txt")
		self.rp.read()
		self.delay = self.get_delay() # how much to wait		
		self.number_followed = 0 # no. of pages followed	
		self.multi_content = 0 # number of times multiple content tags have been found
		self.not_followed = 0 # number of pages that we could not follow	
		self.total_links = 0
		self.scraper = Scraper()
		print "Web Crawler initialized"		

	def get_delay(self): # parse non-standard robots.txt request-rate and crawl-delay directives
		robots = urllib2.urlopen("http://ir.inf.ed.ac.uk/robots.txt").read()
		delays_regexp = re.compile("(user-agent|request-rate|crawl-delay):[ \t]*(.*)", re.IGNORECASE)
		delays_instructions = delays_regexp.findall(robots)
		agent_found = 0
		crawl_delay = 0
		request_rate = 0
		for i in delays_instructions:
			if i[0].lower() == "user-agent" and (i[1] == "TTS" or i[1] == "*"): 
				agent_found = 1
			elif agent_found == 1 and i[0].lower() == "crawl-delay":
				crawl_delay = float(i[1])
			elif agent_found == 1 and i[0].lower() == "request-rate":
				request_rate = float(i[1].split('/')[0])/float(i[1].split('/')[1])
			elif i[0].lower() == "user-agent" and (i[1] != "TTS" or i[1] == "*"):
				agent_found = 0	

		return max(crawl_delay, request_rate)

	def crawl(self):
		url_pair = heapq.heappop(self.frontier)
		self.total_links += 1				
		try:
			while url_pair != '':
				link = url_pair[1]
				#print "this is new url", link
				if(link[0] != "h"):
					link = "http://ir.inf.ed.ac.uk/tts/0837795/" + link
				if self.rp.can_fetch('TTS', link):
					html, self.not_followed = self.scraper.open(link, self.not_followed)
					if html!= None:
						text = html.read()
						updated = self.scraper.updated_content(text)
						# testing to see if we are allowed to crawl this page		
						if (link not in self.followed) or (updated ==1):	
							print "Crawling:", link			
							self.followed.append(link)
							self.process_page(text)
							self.number_followed +=1
							print "Total no. of followed pages:", self.number_followed
							url_pair = heapq.heappop(self.frontier)
							time.sleep(self.delay)
						else:
							url_pair = heapq.heappop(self.frontier)
					else:
						url_pair = heapq.heappop(self.frontier)
				else:
					url_pair = heapq.heappop(self.frontier)
					#print "this is the frontier ", self.frontier 
		except IndexError:
			print "Frontline heapqueue is now empty."
			print "Total no. of followed pages:", self.number_followed
			print "Total no. of (of non-unique) pages that could not be followed:", self.not_followed
			print "Total links extracted:", self.total_links
			print "Total pages with multiple content tags:", str(self.multi_content)
			print "Delay between requests: ", self.delay

	def process_page(self, text):
		text, self.multi_content = self.scraper.grab_content(text, self.multi_content)	
		anchor_regexp = re.compile('<a\s*\S*\s*href=[\'|"](.*?)[\'|"].*?>')
		links = anchor_regexp.findall(text) # fetch all the links
		for i in list(xrange(len(links))):
			link = links.pop(0)
			if link != '#':
				self.total_links +=1
				prio_regexp = re.compile('[0-9][0-9]*[^.html]')
				priority = prio_regexp.findall(link)
				priority_last = priority[len(priority)-1] # retain only the last element found by the regexp, the one that represents the number of the page and implicitly the priority
				print "Adding link:", link						
				if link not  in self.followed :
					heapq.heappush(self.frontier, (9999999-int(priority_last), link)) # add to priority queue
		



class Scraper(object):
	def open(self,url, not_followed): 
		try :
			html = urllib2.urlopen(url)
		except urllib2.HTTPError, error:
			not_followed += 1
			print "Could not follow: " + url + " The error code: " + str(error.code)
			print url
			return None, not_followed
		except urllib2.URLError, uerror:
			print "Could not follow: " + url + " Reason: " + uerror.reason()
			return None, not_followed
		return html, not_followed

	def grab_content(self,text, multi_content):
		content_begin = re.findall('<!-- CONTENT -->', text) #find <!-- CONTENT --> 
		content_end = re.findall('<!-- /CONTENT -->', text) #find <!-- /CONTENT --> 
		if len(content_begin)>1 or len(content_end)>1 :
			multi_content += 1
			print "Multiple content tags have been found"
		if content_begin != [] and content_end != []:
			text = text[text.find('<!-- CONTENT -->')+16:text.find('<!-- /CONTENT -->')]
		else:
			text =""
		return text, multi_content

	def updated_content(self, text):
		checksum = hashlib.sha224(text).hexdigest()
		sumsfile = open('sums', 'w+').readlines()
		for f in sumsfile:
			if f != checksum:
				sumsfile = open('sums', 'a')
				sumsfile.write(checksum)
				sumsfile.write('\n')
				return 1
			else:
				return 0;

		

def main():
	frontier = []
	heapq.heappush(frontier, (9999999-837795, "http://ir.inf.ed.ac.uk/tts/0837795/0837795.html"))
	crawler = Crawler(frontier)
	crawler.crawl()

if __name__ == "__main__":
	start = time.time()
	main()
	finish = time.time()
	print "Running time:", (finish-start)
