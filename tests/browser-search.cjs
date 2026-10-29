"use strict";
// No browser-dependent DOM library: execute production search/render code in a small DOM harness.
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const site = process.env.ICON_ATLAS_SITE ? path.resolve(process.env.ICON_ATLAS_SITE) : path.join(root, 'site');
class Element {
  constructor(id='') {this.id=id;this.value='';this.hidden=false;this.style={};this.children=[];this.listeners={};this.textContent='';this.checked=false;}
  append(...children){this.children.push(...children);}
  appendChild(child){this.children.push(child);return child;}
  replaceChildren(...children){this.children=[...children];}
  addEventListener(type,callback){this.listeners[type]=callback;}
  setAttribute(){}
}
const elements = new Map();
const document = {
  getElementById(id){if(!elements.has(id))elements.set(id,new Element(id));return elements.get(id);},
  createElement(type){return new Element(type);},
  createDocumentFragment(){return new Element('fragment');},
};
const window = {};
const ctx={window,document,location:{search:'',href:'http://localhost/'},URL,URLSearchParams,history:{replaceState(){}},setTimeout,clearTimeout,console};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(site,'catalog-data.js'),'utf8'),ctx);
vm.runInContext(fs.readFileSync(path.join(root,'web/app.js'),'utf8'),ctx);
const search = document.getElementById('search');
const count = document.getElementById('count');
for(const [term,expected] of [['fire',1],['flame',1],['picture',3],['lambda',1],['terminal',1]]) {
  search.value=term;
  search.listeners.input();
  const found=Number(count.textContent.split(' ')[0].replaceAll(',',''));
  if(found<expected)throw new Error(`${term}: expected at least ${expected}, got ${found}`);
  console.log(`${term}: ${found} search results`);
}
const subject=document.getElementById('subject');
if(!subject.children.length)throw new Error('Subject filter failed to populate');
const style=document.getElementById('style');
if(!style.children.length)throw new Error('Style filter failed to populate');
console.log('Browser search and dynamic facet controls: PASS');
