from AgentModule.app import get_html, set_selector, scrape, get_selector_performance_tool
import json

url='https://www.meesho.com/search?q=kurthi'
plat='meesho'

print('STEP1 get_html')
get_html(url)

print('STEP2 set selectors')
sel={
  'product_container':{'type':'css','selectors':["div[data-testid='product-card']","div[class*='ProductCard']","div[class*='Card']","a[href*='/item']","a[href*='/p/']","li","article"]},
  'name':{'type':'css','selectors':['a[title]','h1','h2','h3','p','span']},
  'current_price':{'type':'css','selectors':["span:contains(â‚¹)","[class*='price']","[class*='Price']","span[class*='price']"]},
  'original_price':{'type':'css','selectors':['s','.strike',"[class*='mrp']","span[class*='strike']"]},
  'rating':{'type':'css','selectors':["[aria-label*='out of']","span[class*='rating']","div[class*='rating']"]},
  'reviews':{'type':'css','selectors':["span:contains(Reviews)","span:contains(ratings)","[class*='review']"]},
  'discount':{'type':'css','selectors':["span:contains(% off)","span[class*='discount']","[class*='Off']"]}
}
for k,v in sel.items():
    set_selector(k, v['type'], v['selectors'])

print('STEP3 scrape')
res = scrape(sel, plat)
perf = get_selector_performance_tool() or {}
fp = perf.get('field_performance', {})
fields=['name','current_price','original_price','rating','reviews','discount']
rates = {f:(fp.get(f) or {}).get('success_rate') for f in fields}
print(json.dumps({'platform':plat,'scraped_count':res.get('products_count'),'field_success_rates':rates}, ensure_ascii=False))
