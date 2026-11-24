// Synthetic annotation tests only: no browser, network, model, or real catalog execution.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const html = fs.readFileSync(path.join(__dirname, '../tools/annotation_template.html'), 'utf8');
const script = html.match(/<script>\s*([\s\S]*?)<\/script>/)[1];
class Element {
  constructor(tag='div') { this.tag=tag; this.children=[]; this.attributes={}; this._value=''; this.selectedIndex=0; this.checked=false; this.textContent=''; }
  append(...items) {this.children.push(...items);}
  replaceChildren() {this.children=[];}
  setAttribute(k,v) {this.attributes[k]=v;}
  get value() {return this.tag==='select' ? this.children[this.selectedIndex]?.value : this._value;}
  set value(v) {this._value=v; if(this.tag==='select')this.selectedIndex=this.children.findIndex(c=>c.value===v);}
  click() {if(this.tag==='a')downloads.push(this);}
}
let downloads=[];
const rows=[{query_id:'q1',slot:'women_shoes',product_id:'1',query:'Đi ăn cưới',budget:'700000',price:'300000',product_name:'Giày "A"',description:'Mô tả\nđầy đủ',image_url:'https://example.com/a.jpg',inventory_status:'available',grade:'',annotator:'',notes:''}];
const packet={role:'train-validation',pool_sha256:'pool1',filename:'judgments.csv',rows,columns:Object.keys(rows[0])};
const ids={};for(const id of ['data','role','queries','name','start','backup','restore','csv','main','message','progress','query','budget','coverage','queryProgress','prev','next','products','pending'])ids[id]=new Element(id==='queries'?'select':'div');
ids.data.textContent=JSON.stringify(packet);
const memory=new Map(),blobs=[];
const context=vm.createContext({document:{getElementById:id=>ids[id],createElement:tag=>new Element(tag)},localStorage:{getItem:k=>memory.get(k),setItem:(k,v)=>memory.set(k,v)},Blob,URL:{createObjectURL:b=>{blobs.push(b);return 'blob:fixture'},revokeObjectURL(){}},setTimeout:f=>f(),confirm:()=>false,console});
(async()=>{
  vm.runInContext(script,context);
  ids.start.onclick();assert.match(ids.message.textContent,/Nhập tên/);
  ids.name.value='tester';ids.start.onclick();assert.equal(ids.main.hidden,false);
  ids.csv.onclick();assert.equal(downloads.at(-1).download,'PARTIAL-judgments.csv');
  assert.match(await blobs.at(-1).text(),/"grade","annotator"/);
  vm.runInContext("labels[key(packet.rows[0])]={grade:'0',notes:'Ghi chú, có dấu và \\\"trích dẫn\\\"'};save();render();",context);
  ids.csv.onclick();assert.equal(downloads.at(-1).download,'judgments.csv');
  const csv=await blobs.at(-1).text();assert.match(csv,/"0","tester"/);assert.match(csv,/"Giày ""A"""/);
  assert.equal(memory.size,1);assert.match([...memory.keys()][0],/pool1:train-validation:tester$/);
  ids.backup.onclick();const draft=JSON.parse(await blobs.at(-1).text());assert.equal(draft.role,'train-validation');assert.equal(draft.annotator,'tester');
  ids.restore.files=[{text:async()=>JSON.stringify({...draft,role:'test-a'})}];await ids.restore.onchange();assert.match(ids.message.textContent,/khác bộ dữ liệu, vai trò hoặc người chấm/);
  assert.throws(()=>vm.runInContext("validateLabels({'unknown':{grade:'3',notes:''}})",context),/không hợp lệ/);
  console.log('PASS: empty annotations stay blank, grade 0 exports, CSV quoting, identity-scoped persistence, backup and incompatible restore rejection.');
})().catch(e=>{console.error(e);process.exitCode=1});
