import{S as D,i as S,s as L,e as b,t as B,a as w,b as k,c as p,l as N,d as M,n as O,f as y,g as V,h as R,j as X,r as K,k as P,m as I,o as A,p as g,q as v,u as F,v as E,w as U,x as Y,y as $,z as Z,F as Le,A as H,B as Q,C as je,D as Ne,E as x}from"./vendor.e94bbfaf.js";const Oe=function(){const e=document.createElement("link").relList;if(e&&e.supports&&e.supports("modulepreload"))return;for(const n of document.querySelectorAll('link[rel="modulepreload"]'))t(n);new MutationObserver(n=>{for(const s of n)if(s.type==="childList")for(const r of s.addedNodes)r.tagName==="LINK"&&r.rel==="modulepreload"&&t(r)}).observe(document,{childList:!0,subtree:!0});function l(n){const s={};return n.integrity&&(s.integrity=n.integrity),n.referrerpolicy&&(s.referrerPolicy=n.referrerpolicy),n.crossorigin==="use-credentials"?s.credentials="include":n.crossorigin==="anonymous"?s.credentials="omit":s.credentials="same-origin",s}function t(n){if(n.ep)return;n.ep=!0;const s=l(n);fetch(n.href,s)}};Oe();function Te(i){let e,l,t,n,s,r,c;return{c(){e=b("div"),l=b("mark"),t=b("span"),n=B(i[0]),s=b("button"),s.textContent="x",w(e,"class","calculation svelte-ws2txc")},m(a,o){k(a,e,o),p(e,l),p(l,t),p(t,n),p(l,s),r||(c=N(s,"click",i[1]),r=!0)},p(a,[o]){o&1&&M(n,a[0])},i:O,o:O,d(a){a&&y(e),r=!1,c()}}}function Be(i,e,l){let{id:t}=e,{name:n}=e;const s=V(),r=()=>s("closeItemClick",{id:t});return i.$$set=c=>{"id"in c&&l(2,t=c.id),"name"in c&&l(0,n=c.name)},[n,r,t]}class Ee extends D{constructor(e){super();S(this,e,Be,Te,L,{id:2,name:0})}}function ee(i){let e,l;return{c(){e=b("p"),l=B(i[1]),w(e,"class","description svelte-b1dmlw")},m(t,n){k(t,e,n),p(e,l)},p(t,n){n&2&&M(l,t[1])},d(t){t&&y(e)}}}function $e(i){let e,l,t,n,s,r,c=i[1]&&ee(i);return{c(){e=b("div"),l=b("div"),t=b("span"),n=R(),c&&c.c(),w(l,"class","header svelte-b1dmlw"),w(e,"class","wrapper svelte-b1dmlw"),X(e,"selected",i[2])},m(a,o){k(a,e,o),p(e,l),p(l,t),t.innerHTML=i[0],p(e,n),c&&c.m(e,null),s||(r=[N(e,"click",i[3]),N(e,"mouseover",i[4]),N(e,"focus",i[4])],s=!0)},p(a,[o]){o&1&&(t.innerHTML=a[0]),a[1]?c?c.p(a,o):(c=ee(a),c.c(),c.m(e,null)):c&&(c.d(1),c=null),o&4&&X(e,"selected",a[2])},i:O,o:O,d(a){a&&y(e),c&&c.d(),s=!1,K(r)}}}function Me(i,e,l){const t=V();let{id:n}=e,{name:s}=e,{description:r}=e,{selected:c}=e;const a=()=>t("clickItem",{id:n}),o=()=>t("hoverItem",{id:n});return i.$$set=f=>{"id"in f&&l(5,n=f.id),"name"in f&&l(0,s=f.name),"description"in f&&l(1,r=f.description),"selected"in f&&l(2,c=f.selected)},[s,r,c,a,o,n]}class Ve extends D{constructor(e){super();S(this,e,Me,$e,L,{id:5,name:0,description:1,selected:2})}}function te(i,e,l){const t=i.slice();return t[7]=e[l].id,t[8]=e[l].name,t[9]=e[l].highlightedName,t[10]=e[l].description,t[12]=l,t}function le(i,e){let l,t,n;return t=new Ve({props:{id:e[7],name:e[9]||e[8],description:e[10],selected:e[12]===e[1]}}),t.$on("hoverItem",e[2]),t.$on("clickItem",e[3]),{key:i,first:null,c(){l=P(),I(t.$$.fragment),this.first=l},m(s,r){k(s,l,r),A(t,s,r),n=!0},p(s,r){e=s;const c={};r&1&&(c.id=e[7]),r&1&&(c.name=e[9]||e[8]),r&1&&(c.description=e[10]),r&3&&(c.selected=e[12]===e[1]),t.$set(c)},i(s){n||(g(t.$$.fragment,s),n=!0)},o(s){v(t.$$.fragment,s),n=!1},d(s){s&&y(l),F(t,s)}}}function Qe(i){let e,l=[],t=new Map,n,s=i[0];const r=c=>c[7];for(let c=0;c<s.length;c+=1){let a=te(i,s,c),o=r(a);t.set(o,l[c]=le(o,a))}return{c(){e=b("div");for(let c=0;c<l.length;c+=1)l[c].c();w(e,"class","calculation-list svelte-1gzkwp7")},m(c,a){k(c,e,a);for(let o=0;o<l.length;o+=1)l[o].m(e,null);n=!0},p(c,[a]){a&15&&(s=c[0],E(),l=U(l,a,r,1,c,s,t,e,Y,le,null,te),$())},i(c){if(!n){for(let a=0;a<s.length;a+=1)g(l[a]);n=!0}},o(c){for(let a=0;a<l.length;a+=1)v(l[a]);n=!1},d(c){c&&y(e);for(let a=0;a<l.length;a+=1)l[a].d()}}}function ze(i,e,l){let t,{calculations:n}=e,{selectedIndex:s}=e;const r=V(),c=f=>{let u=t.indexOf(f);return u>-1?u:null},a=f=>{r("hoverItem",{index:c(f.detail.id)})},o=f=>{r("clickItem",{index:c(f.detail.id)})};return i.$$set=f=>{"calculations"in f&&l(0,n=f.calculations),"selectedIndex"in f&&l(1,s=f.selectedIndex)},i.$$.update=()=>{i.$$.dirty&1&&(t=n.map(f=>f.id))},[n,s,a,o]}class Pe extends D{constructor(e){super();S(this,e,ze,Qe,L,{calculations:0,selectedIndex:1})}}function ne(i){let e,l,t;return{c(){e=b("input"),w(e,"placeholder",i[1]),w(e,"class","svelte-ysf8qw")},m(n,s){k(n,e,s),Z(e,i[2]),l||(t=[N(e,"input",i[12]),N(e,"focus",i[6]),N(e,"blur",i[7]),N(e,"keydown",i[9])],l=!0)},p(n,s){s&2&&w(e,"placeholder",n[1]),s&4&&e.value!==n[2]&&Z(e,n[2])},d(n){n&&y(e),l=!1,K(t)}}}function ie(i){let e,l;return e=new Pe({props:{calculations:i[5],selectedIndex:i[3]}}),e.$on("hoverItem",i[8]),e.$on("clickItem",i[10]),{c(){I(e.$$.fragment)},m(t,n){A(e,t,n),l=!0},p(t,n){const s={};n&32&&(s.calculations=t[5]),n&8&&(s.selectedIndex=t[3]),e.$set(s)},i(t){l||(g(e.$$.fragment,t),l=!0)},o(t){v(e.$$.fragment,t),l=!1},d(t){F(e,t)}}}function Ue(i){let e,l,t,n=i[0].length>0&&ne(i),s=i[4]&&ie(i);return{c(){e=b("div"),n&&n.c(),l=R(),s&&s.c(),w(e,"class","svelte-ysf8qw")},m(r,c){k(r,e,c),n&&n.m(e,null),p(e,l),s&&s.m(e,null),t=!0},p(r,[c]){r[0].length>0?n?n.p(r,c):(n=ne(r),n.c(),n.m(e,l)):n&&(n.d(1),n=null),r[4]?s?(s.p(r,c),c&16&&g(s,1)):(s=ie(r),s.c(),g(s,1),s.m(e,null)):s&&(E(),v(s,1,1,()=>{s=null}),$())},i(r){t||(g(s),t=!0)},o(r){v(s),t=!1},d(r){r&&y(e),n&&n.d(),s&&s.d()}}}function He(i,e,l){let t,n,{availableCalculations:s}=e,{placeholder:r}=e,c="",a=0,o=!1,f=new Le(s,{keys:["name"],includeMatches:!0});const u=C=>{let j=C.item.name;return C.matches[0].indices.reverse().forEach(([J,W])=>{j=j.slice(0,J)+"<u>"+j.slice(J,W+1)+"</u>"+j.slice(W+1)}),Object.assign({highlightedName:j},C.item)},d=V(),m=()=>l(4,o=!0),h=()=>setTimeout(()=>l(4,o=!1),10),_=C=>{l(3,a=C.detail.index)},q=C=>{let j=a+C;j>=n.length?l(3,a=0):j<0?l(3,a=n.length-1):l(3,a=j)},T=({key:C,target:j})=>{C=="ArrowDown"?q(1):C=="ArrowUp"?q(-1):C=="Enter"?G(n[a],j):C=="Escape"&&j.blur()},z=C=>{G(n[C.detail.index],C.target)},G=(C,j)=>{d("selectItem",{item:C}),l(2,c=""),j!==null&&j.blur()};function Se(){c=this.value,l(2,c)}return i.$$set=C=>{"availableCalculations"in C&&l(0,s=C.availableCalculations),"placeholder"in C&&l(1,r=C.placeholder)},i.$$.update=()=>{i.$$.dirty&1&&f.setCollection(s),i.$$.dirty&4&&l(11,t=f.search(c)),i.$$.dirty&2053&&l(5,n=c.length>0?t.map(u):s)},[s,r,c,a,o,n,m,h,_,T,z,t,Se]}class se extends D{constructor(e){super();S(this,e,He,Ue,L,{availableCalculations:0,placeholder:1})}}function re(i,e,l){const t=i.slice();return t[8]=e[l].id,t[9]=e[l].name,t[11]=l,t}function ce(i){let e;return{c(){e=B(",")},m(l,t){k(l,e,t)},d(l){l&&y(e)}}}function ae(i,e){let l,t,n,s,r;t=new Ee({props:{id:e[8],name:e[9]}}),t.$on("closeItemClick",e[5]);let c=e[11]<e[3].length-1&&ce();return{key:i,first:null,c(){l=P(),I(t.$$.fragment),n=R(),c&&c.c(),s=P(),this.first=l},m(a,o){k(a,l,o),A(t,a,o),k(a,n,o),c&&c.m(a,o),k(a,s,o),r=!0},p(a,o){e=a;const f={};o&8&&(f.id=e[8]),o&8&&(f.name=e[9]),t.$set(f),e[11]<e[3].length-1?c||(c=ce(),c.c(),c.m(s.parentNode,s)):c&&(c.d(1),c=null)},i(a){r||(g(t.$$.fragment,a),r=!0)},o(a){v(t.$$.fragment,a),r=!1},d(a){a&&y(l),F(t,a),a&&y(n),c&&c.d(a),a&&y(s)}}}function Ke(i){let e,l,t,n,s=[],r=new Map,c,a,o,f=i[3];const u=d=>d[8];for(let d=0;d<f.length;d+=1){let m=re(i,f,d),h=u(m);r.set(h,s[d]=ae(h,m))}return a=new se({props:{availableCalculations:i[2],placeholder:i[1]}}),a.$on("selectItem",i[4]),{c(){e=b("div"),l=b("span"),t=B(i[0]),n=R();for(let d=0;d<s.length;d+=1)s[d].c();c=R(),I(a.$$.fragment),w(e,"class","calculation-selector svelte-1jkx5ha")},m(d,m){k(d,e,m),p(e,l),p(l,t),p(e,n);for(let h=0;h<s.length;h+=1)s[h].m(e,null);p(e,c),A(a,e,null),o=!0},p(d,[m]){(!o||m&1)&&M(t,d[0]),m&40&&(f=d[3],E(),s=U(s,m,u,1,d,f,r,e,Y,ae,c,re),$());const h={};m&4&&(h.availableCalculations=d[2]),m&2&&(h.placeholder=d[1]),a.$set(h)},i(d){if(!o){for(let m=0;m<f.length;m+=1)g(s[m]);g(a.$$.fragment,d),o=!0}},o(d){for(let m=0;m<s.length;m+=1)v(s[m]);v(a.$$.fragment,d),o=!1},d(d){d&&y(e);for(let m=0;m<s.length;m+=1)s[m].d();F(a)}}}function Ge(i,e,l){let{title:t}=e,{placeholder:n}=e,{availableCalculations:s}=e,r=[];const c=V(),a=()=>{c("updateCalculations",{calculations:r})},o=u=>{l(3,r=[...r,u.detail.item]),a()},f=u=>{l(3,r=r.filter(d=>d.id!==u.detail.id)),a()};return i.$$set=u=>{"title"in u&&l(0,t=u.title),"placeholder"in u&&l(1,n=u.placeholder),"availableCalculations"in u&&l(2,s=u.availableCalculations)},[t,n,s,r,o,f]}class oe extends D{constructor(e){super();S(this,e,Ge,Ke,L,{title:0,placeholder:1,availableCalculations:2})}}function Je(i){let e,l,t,n,s,r;return{c(){e=b("div"),l=b("label"),t=b("input"),n=B(i[0]),w(t,"type","checkbox"),t.checked=i[1],w(t,"class","svelte-yg8m7f")},m(c,a){k(c,e,a),p(e,l),p(l,t),p(l,n),s||(r=N(t,"change",i[2]),s=!0)},p(c,[a]){a&2&&(t.checked=c[1]),a&1&&M(n,c[0])},i:O,o:O,d(c){c&&y(e),s=!1,r()}}}function We(i,e,l){let{label:t}=e,{checked:n}=e;const s=V(),r=()=>s("toggle",{label:t});return i.$$set=c=>{"label"in c&&l(0,t=c.label),"checked"in c&&l(1,n=c.checked)},[t,n,r]}class ue extends D{constructor(e){super();S(this,e,We,Je,L,{label:0,checked:1})}}function fe(i,e,l){const t=i.slice();return t[6]=e[l],t}function me(i){let e,l;return e=new ue({props:{label:i[6],checked:i[1].has(i[6])}}),e.$on("toggle",i[4]),{c(){I(e.$$.fragment)},m(t,n){A(e,t,n),l=!0},p(t,n){const s={};n&1&&(s.label=t[6]),n&3&&(s.checked=t[1].has(t[6])),e.$set(s)},i(t){l||(g(e.$$.fragment,t),l=!0)},o(t){v(e.$$.fragment,t),l=!1},d(t){F(e,t)}}}function Xe(i){let e,l,t,n;l=new ue({props:{label:"(All)",checked:i[2]}}),l.$on("toggle",i[3]);let s=i[0],r=[];for(let a=0;a<s.length;a+=1)r[a]=me(fe(i,s,a));const c=a=>v(r[a],1,1,()=>{r[a]=null});return{c(){e=b("div"),I(l.$$.fragment),t=R();for(let a=0;a<r.length;a+=1)r[a].c()},m(a,o){k(a,e,o),A(l,e,null),p(e,t);for(let f=0;f<r.length;f+=1)r[f].m(e,null);n=!0},p(a,[o]){const f={};if(o&4&&(f.checked=a[2]),l.$set(f),o&3){s=a[0];let u;for(u=0;u<s.length;u+=1){const d=fe(a,s,u);r[u]?(r[u].p(d,o),g(r[u],1)):(r[u]=me(d),r[u].c(),g(r[u],1),r[u].m(e,null))}for(E(),u=s.length;u<r.length;u+=1)c(u);$()}},i(a){if(!n){g(l.$$.fragment,a);for(let o=0;o<s.length;o+=1)g(r[o]);n=!0}},o(a){v(l.$$.fragment,a),r=r.filter(Boolean);for(let o=0;o<r.length;o+=1)v(r[o]);n=!1},d(a){a&&y(e),F(l),H(r,a)}}}function Ye(i,e,l){let t,{options:n}=e,{checked:s}=e;const r=V(),c=()=>{r(t?"uncheckAll":"checkAll")};function a(o){Q.call(this,i,o)}return i.$$set=o=>{"options"in o&&l(0,n=o.options),"checked"in o&&l(1,s=o.checked)},i.$$.update=()=>{i.$$.dirty&3&&l(2,t=n.length===Array.from(s).length)},[n,s,t,c,a]}class Ze extends D{constructor(e){super();S(this,e,Ye,Xe,L,{options:0,checked:1})}}function xe(i){let e,l,t,n,s,r,c,a,o;return t=new Ze({props:{options:i[0],checked:i[1]}}),t.$on("toggle",i[3]),t.$on("checkAll",i[4]),t.$on("uncheckAll",i[5]),{c(){e=b("div"),l=b("div"),I(t.$$.fragment),n=R(),s=b("div"),r=b("button"),r.textContent="Apply",w(l,"class","checkbox-list svelte-t4ra3u"),w(s,"class","filter-apply svelte-t4ra3u"),w(e,"class","values-filter svelte-t4ra3u")},m(f,u){k(f,e,u),p(e,l),A(t,l,null),p(e,n),p(e,s),p(s,r),c=!0,a||(o=N(r,"click",i[2]),a=!0)},p(f,[u]){const d={};u&1&&(d.options=f[0]),u&2&&(d.checked=f[1]),t.$set(d)},i(f){c||(g(t.$$.fragment,f),c=!0)},o(f){v(t.$$.fragment,f),c=!1},d(f){f&&y(e),F(t),a=!1,o()}}}function et(i,e,l){let{values:t}=e,{checked:n}=e;const s=V(),r=()=>{s("apply")};function c(f){Q.call(this,i,f)}function a(f){Q.call(this,i,f)}function o(f){Q.call(this,i,f)}return i.$$set=f=>{"values"in f&&l(0,t=f.values),"checked"in f&&l(1,n=f.checked)},[t,n,r,c,a,o]}class tt extends D{constructor(e){super();S(this,e,et,xe,L,{values:0,checked:1})}}function de(i){let e,l,t,n,s;return{c(){e=b("button"),e.textContent="values",l=R(),t=b("button"),t.textContent="range"},m(r,c){k(r,e,c),k(r,l,c),k(r,t,c),n||(s=[N(e,"click",i[4]),N(t,"click",i[5])],n=!0)},p:O,d(r){r&&y(e),r&&y(l),r&&y(t),n=!1,K(s)}}}function he(i){let e,l;return e=new tt({props:{values:i[0].values,checked:i[1].values}}),e.$on("toggle",i[6]),e.$on("apply",i[7]),e.$on("checkAll",i[8]),e.$on("uncheckAll",i[9]),{c(){I(e.$$.fragment)},m(t,n){A(e,t,n),l=!0},p(t,n){const s={};n&1&&(s.values=t[0].values),n&2&&(s.checked=t[1].values),e.$set(s)},i(t){l||(g(e.$$.fragment,t),l=!0)},o(t){v(e.$$.fragment,t),l=!1},d(t){F(e,t)}}}function lt(i){let e,l,t,n=i[3]&&de(i),s=i[2]==="values"&&he(i);return{c(){e=b("div"),n&&n.c(),l=R(),s&&s.c(),w(e,"class","svelte-l5398h")},m(r,c){k(r,e,c),n&&n.m(e,null),p(e,l),s&&s.m(e,null),t=!0},p(r,[c]){r[3]?n?n.p(r,c):(n=de(r),n.c(),n.m(e,l)):n&&(n.d(1),n=null),r[2]==="values"?s?(s.p(r,c),c&4&&g(s,1)):(s=he(r),s.c(),g(s,1),s.m(e,null)):s&&(E(),v(s,1,1,()=>{s=null}),$())},i(r){t||(g(s),t=!0)},o(r){v(s),t=!1},d(r){r&&y(e),n&&n.d(),s&&s.d()}}}function nt(i,e,l){let t,{info:n}=e,{state:s}=e,r=n.values!==null?"values":"range";const c=()=>l(2,r="values"),a=()=>l(2,r="range");function o(m){Q.call(this,i,m)}function f(m){Q.call(this,i,m)}function u(m){Q.call(this,i,m)}function d(m){Q.call(this,i,m)}return i.$$set=m=>{"info"in m&&l(0,n=m.info),"state"in m&&l(1,s=m.state)},i.$$.update=()=>{i.$$.dirty&1&&l(3,t=n.values!==null&&n.range!==null)},[n,s,r,t,c,a,o,f,u,d]}class it extends D{constructor(e){super();S(this,e,nt,lt,L,{info:0,state:1})}}function _e(i){let e,l;return e=new it({props:{info:i[0].info,state:i[0].state}}),e.$on("apply",i[6]),e.$on("toggle",i[3]),e.$on("checkAll",i[4]),e.$on("uncheckAll",i[5]),{c(){I(e.$$.fragment)},m(t,n){A(e,t,n),l=!0},p(t,n){const s={};n&1&&(s.info=t[0].info),n&1&&(s.state=t[0].state),e.$set(s)},i(t){l||(g(e.$$.fragment,t),l=!0)},o(t){v(e.$$.fragment,t),l=!1},d(t){F(e,t)}}}function st(i){let e,l,t=i[0].dimension.name+"",n,s,r,c,a,o,f,u=i[0].info!==null&&i[1]&&_e(i);return{c(){e=b("div"),l=b("mark"),n=B(t),s=R(),r=b("button"),r.textContent="\u270D\uFE0F",c=R(),u&&u.c(),w(e,"class","filter svelte-4szduf")},m(d,m){k(d,e,m),p(e,l),p(l,n),p(e,s),p(e,r),p(e,c),u&&u.m(e,null),a=!0,o||(f=N(r,"click",i[2]),o=!0)},p(d,[m]){(!a||m&1)&&t!==(t=d[0].dimension.name+"")&&M(n,t),d[0].info!==null&&d[1]?u?(u.p(d,m),m&3&&g(u,1)):(u=_e(d),u.c(),g(u,1),u.m(e,null)):u&&(E(),v(u,1,1,()=>{u=null}),$())},i(d){a||(g(u),a=!0)},o(d){v(u),a=!1},d(d){d&&y(e),u&&u.d(),o=!1,f()}}}function rt(i,e,l){let{filter:t}=e,n=!0;const s=()=>l(1,n=!n),r=V(),c=u=>{r("toggle",{label:u.detail.label,id:t.dimension.id})},a=()=>{r("checkAll",{id:t.dimension.id})},o=()=>{r("uncheckAll",{id:t.dimension.id})};function f(u){Q.call(this,i,u)}return i.$$set=u=>{"filter"in u&&l(0,t=u.filter)},[t,n,s,c,a,o,f]}class ct extends D{constructor(e){super();S(this,e,rt,st,L,{filter:0})}}function at(i){const e=i.query;if(e===null||i.info.values.length===Array.from(e.values).length)return null;if(typeof e.values!="undefined")return ft(i.dimension.id,e.values)}function ot(i){return typeof i=="string"?`'${i}'`:`${i}`}function ut(i){return`(${i.map(ot).join(", ")})`}function ft(i,e){const l=ut(e);return l==="()"?"false":`:${i} IN ${l}`}function ge(i,e,l){const t=i.slice();return t[12]=e[l],t}function pe(i){let e,l;return e=new ct({props:{filter:i[12]}}),e.$on("toggle",i[5]),e.$on("checkAll",i[6]),e.$on("uncheckAll",i[7]),{c(){I(e.$$.fragment)},m(t,n){A(e,t,n),l=!0},p(t,n){const s={};n&8&&(s.filter=t[12]),e.$set(s)},i(t){l||(g(e.$$.fragment,t),l=!0)},o(t){v(e.$$.fragment,t),l=!1},d(t){F(e,t)}}}function mt(i){let e,l,t,n,s,r,c,a=i[3],o=[];for(let u=0;u<a.length;u+=1)o[u]=pe(ge(i,a,u));const f=u=>v(o[u],1,1,()=>{o[u]=null});return r=new se({props:{availableCalculations:i[2],placeholder:i[1]}}),r.$on("selectItem",i[4]),{c(){e=b("div"),l=b("span"),t=B(i[0]),n=R();for(let u=0;u<o.length;u+=1)o[u].c();s=R(),I(r.$$.fragment)},m(u,d){k(u,e,d),p(e,l),p(l,t),p(e,n);for(let m=0;m<o.length;m+=1)o[m].m(e,null);p(e,s),A(r,e,null),c=!0},p(u,[d]){if((!c||d&1)&&M(t,u[0]),d&232){a=u[3];let h;for(h=0;h<a.length;h+=1){const _=ge(u,a,h);o[h]?(o[h].p(_,d),g(o[h],1)):(o[h]=pe(_),o[h].c(),g(o[h],1),o[h].m(e,s))}for(E(),h=a.length;h<o.length;h+=1)f(h);$()}const m={};d&4&&(m.availableCalculations=u[2]),d&2&&(m.placeholder=u[1]),r.$set(m)},i(u){if(!c){for(let d=0;d<a.length;d+=1)g(o[d]);g(r.$$.fragment,u),c=!0}},o(u){o=o.filter(Boolean);for(let d=0;d<o.length;d+=1)v(o[d]);v(r.$$.fragment,u),c=!1},d(u){u&&y(e),H(o,u),F(r)}}}function dt(i){return Object.assign(i,{state:{range:i.info.range,values:new Set(i.info.values)},query:null})}function ht(i,e,l){let t,{title:n}=e,{placeholder:s}=e,{availableDimensions:r}=e,c=[];const a=V(),o=_=>{f(_.detail.item.id)};function f(_){fetch(`/api/filter/${_}`,{method:"GET"}).then(q=>q.json()).then(q=>{l(3,c=[...c,dt(q)])}).catch(q=>console.log(q))}function u(_){l(3,c=c.map(q=>{const{id:T,label:z}=_.detail;return q.dimension.id===T&&(q.state.values.delete(z)||q.state.values.add(z)),q.query={values:Array.from(q.state.values)},q}))}function d(_,q=!1){l(3,c=c.map(T=>(T.dimension.id===_&&(q?T.state.values=new Set:T.state.values=new Set(T.info.values),T.query={values:Array.from(T.state.values)}),T)))}function m(_){d(_.detail.id)}function h(_){d(_.detail.id,!0)}return i.$$set=_=>{"title"in _&&l(0,n=_.title),"placeholder"in _&&l(1,s=_.placeholder),"availableDimensions"in _&&l(2,r=_.availableDimensions)},i.$$.update=()=>{i.$$.dirty&8&&l(8,t=c.map(at).filter(_=>_!==null)),i.$$.dirty&256&&a("updateFilters",t)},[n,s,r,c,o,u,m,h,t]}class _t extends D{constructor(e){super();S(this,e,ht,mt,L,{title:0,placeholder:1,availableDimensions:2})}}function gt(i){let e,l,t,n,s,r;return{c(){e=b("div"),l=b("h1"),t=B(i[0]),n=R(),s=b("span"),r=B(i[1]),w(l,"class","svelte-mi0gkn"),w(s,"class","svelte-mi0gkn"),w(e,"class","svelte-mi0gkn")},m(c,a){k(c,e,a),p(e,l),p(l,t),p(e,n),p(e,s),p(s,r)},p(c,[a]){a&1&&M(t,c[0]),a&2&&M(r,c[1])},i:O,o:O,d(c){c&&y(e)}}}function pt(i,e,l){let t,{name:n}=e,{value:s}=e,{format:r=null}=e;return i.$$set=c=>{"name"in c&&l(0,n=c.name),"value"in c&&l(2,s=c.value),"format"in c&&l(3,r=c.format)},i.$$.update=()=>{i.$$.dirty&12&&l(1,t=s)},[n,t,s,r]}class bt extends D{constructor(e){super();S(this,e,pt,gt,L,{name:0,value:2,format:3})}}const be=i=>i;function vt(i,e){if(typeof e=="undefined"||e===null)return be;const l=e.currency_prefix.length>0||e.currency_suffix.length>0?[e.currency_prefix,e.currency_suffix]:i.currency,t=Object.assign({},i,{currency:l});return je(t).format(e.spec)}function kt(i,e){if(typeof e=="undefined"||e===null)return be;const t=Ne(i).format(e.spec);return n=>{const s=new Date(n);return t(s)}}function ve(i){let e={};return Object.keys(i.columns).forEach(l=>{const t=i.columns[l];t.type==="time"?e[l]=kt(i.locale.time,t.format):e[l]=vt(i.locale.number,t.format)}),e}function ke(i,e,l){const t=i.slice();return t[3]=e[l].name,t[4]=e[l].value,t}function ye(i){let e,l;return e=new bt({props:{name:i[3],value:i[4]}}),{c(){I(e.$$.fragment)},m(t,n){A(e,t,n),l=!0},p(t,n){const s={};n&1&&(s.name=t[3]),n&1&&(s.value=t[4]),e.$set(s)},i(t){l||(g(e.$$.fragment,t),l=!0)},o(t){v(e.$$.fragment,t),l=!1},d(t){F(e,t)}}}function yt(i){let e,l,t=i[0],n=[];for(let r=0;r<t.length;r+=1)n[r]=ye(ke(i,t,r));const s=r=>v(n[r],1,1,()=>{n[r]=null});return{c(){e=b("div");for(let r=0;r<n.length;r+=1)n[r].c();w(e,"class","big-numbers svelte-s599iq")},m(r,c){k(r,e,c);for(let a=0;a<n.length;a+=1)n[a].m(e,null);l=!0},p(r,[c]){if(c&1){t=r[0];let a;for(a=0;a<t.length;a+=1){const o=ke(r,t,a);n[a]?(n[a].p(o,c),g(n[a],1)):(n[a]=ye(o),n[a].c(),g(n[a],1),n[a].m(e,null))}for(E(),a=t.length;a<n.length;a+=1)s(a);$()}},i(r){if(!l){for(let c=0;c<t.length;c+=1)g(n[c]);l=!0}},o(r){n=n.filter(Boolean);for(let c=0;c<n.length;c+=1)v(n[c]);l=!1},d(r){r&&y(e),H(n,r)}}}function wt(i,e,l){let t,{queryResult:n}=e,s=[];return i.$$set=r=>{"queryResult"in r&&l(1,n=r.queryResult)},i.$$.update=()=>{if(i.$$.dirty&2&&l(2,t=ve(n.metadata)),i.$$.dirty&6&&n.data.length===1){const r=n.data[0],c=n.metadata.columns;l(0,s=Object.keys(r).map(a=>({name:c[a].name,value:t[a](r[a])})))}},[s,n,t]}class Ct extends D{constructor(e){super();S(this,e,wt,yt,L,{queryResult:1})}}function we(i,e,l){const t=i.slice();return t[4]=e[l],t}function Ce(i,e,l){const t=i.slice();return t[7]=e[l],t}function qe(i,e,l){const t=i.slice();return t[10]=e[l],t}function Ie(i,e){let l,t=e[10]+"",n;return{key:i,first:null,c(){l=b("th"),n=B(t),w(l,"class","svelte-10mmylh"),this.first=l},m(s,r){k(s,l,r),p(l,n)},p(s,r){e=s,r&8&&t!==(t=e[10]+"")&&M(n,t)},d(s){s&&y(l)}}}function Ae(i,e){let l,t=e[2][e[7]](e[4][e[7]])+"",n;return{key:i,first:null,c(){l=b("td"),n=B(t),w(l,"class","svelte-10mmylh"),this.first=l},m(s,r){k(s,l,r),p(l,n)},p(s,r){e=s,r&7&&t!==(t=e[2][e[7]](e[4][e[7]])+"")&&M(n,t)},d(s){s&&y(l)}}}function Fe(i){let e,l=[],t=new Map,n,s=i[1];const r=c=>c[7];for(let c=0;c<s.length;c+=1){let a=Ce(i,s,c),o=r(a);t.set(o,l[c]=Ae(o,a))}return{c(){e=b("tr");for(let c=0;c<l.length;c+=1)l[c].c();n=R()},m(c,a){k(c,e,a);for(let o=0;o<l.length;o+=1)l[o].m(e,null);p(e,n)},p(c,a){a&7&&(s=c[1],l=U(l,a,r,1,c,s,t,e,x,Ae,n,Ce))},d(c){c&&y(e);for(let a=0;a<l.length;a+=1)l[a].d()}}}function qt(i){let e,l,t,n,s=[],r=new Map,c,a,o=i[3];const f=m=>m[10];for(let m=0;m<o.length;m+=1){let h=qe(i,o,m),_=f(h);r.set(_,s[m]=Ie(_,h))}let u=i[0].data,d=[];for(let m=0;m<u.length;m+=1)d[m]=Fe(we(i,u,m));return{c(){e=b("div"),l=b("table"),t=b("thead"),n=b("tr");for(let m=0;m<s.length;m+=1)s[m].c();c=R(),a=b("tbody");for(let m=0;m<d.length;m+=1)d[m].c();w(l,"class","svelte-10mmylh"),w(e,"class","table-wrapper svelte-10mmylh")},m(m,h){k(m,e,h),p(e,l),p(l,t),p(t,n);for(let _=0;_<s.length;_+=1)s[_].m(n,null);p(l,c),p(l,a);for(let _=0;_<d.length;_+=1)d[_].m(a,null)},p(m,[h]){if(h&8&&(o=m[3],s=U(s,h,f,1,m,o,r,n,x,Ie,null,qe)),h&7){u=m[0].data;let _;for(_=0;_<u.length;_+=1){const q=we(m,u,_);d[_]?d[_].p(q,h):(d[_]=Fe(q),d[_].c(),d[_].m(a,null))}for(;_<d.length;_+=1)d[_].d(1);d.length=u.length}},i:O,o:O,d(m){m&&y(e);for(let h=0;h<s.length;h+=1)s[h].d();H(d,m)}}}function It(i,e,l){let t,n,s,{queryResult:r}=e;return i.$$set=c=>{"queryResult"in c&&l(0,r=c.queryResult)},i.$$.update=()=>{i.$$.dirty&1&&l(1,t=Object.keys(r.metadata.columns)),i.$$.dirty&3&&l(3,n=t.map(c=>r.metadata.columns[c].name)),i.$$.dirty&1&&l(2,s=ve(r.metadata))},[r,t,s,n]}class At extends D{constructor(e){super();S(this,e,It,qt,L,{queryResult:0})}}function Ft(i){let e,l;return e=new At({props:{queryResult:i[0]}}),{c(){I(e.$$.fragment)},m(t,n){A(e,t,n),l=!0},p(t,n){const s={};n&1&&(s.queryResult=t[0]),e.$set(s)},i(t){l||(g(e.$$.fragment,t),l=!0)},o(t){v(e.$$.fragment,t),l=!1},d(t){F(e,t)}}}function Rt(i){let e,l;return e=new Ct({props:{queryResult:i[0]}}),{c(){I(e.$$.fragment)},m(t,n){A(e,t,n),l=!0},p(t,n){const s={};n&1&&(s.queryResult=t[0]),e.$set(s)},i(t){l||(g(e.$$.fragment,t),l=!0)},o(t){v(e.$$.fragment,t),l=!1},d(t){F(e,t)}}}function Dt(i){let e,l,t,n;const s=[Rt,Ft],r=[];function c(a,o){return a[0].data.length===1?0:a[0].data.length>1?1:-1}return~(e=c(i))&&(l=r[e]=s[e](i)),{c(){l&&l.c(),t=P()},m(a,o){~e&&r[e].m(a,o),k(a,t,o),n=!0},p(a,[o]){let f=e;e=c(a),e===f?~e&&r[e].p(a,o):(l&&(E(),v(r[f],1,1,()=>{r[f]=null}),$()),~e?(l=r[e],l?l.p(a,o):(l=r[e]=s[e](a),l.c()),g(l,1),l.m(t.parentNode,t)):l=null)},i(a){n||(g(l),n=!0)},o(a){v(l),n=!1},d(a){~e&&r[e].d(a),a&&y(t)}}}function St(i,e,l){let{queryResult:t}=e;return i.$$set=n=>{"queryResult"in n&&l(0,t=n.queryResult)},[t]}class Lt extends D{constructor(e){super();S(this,e,St,Dt,L,{queryResult:0})}}function Re(i){let e,l,t,n;return e=new oe({props:{title:"by",placeholder:"add a breakdown...",availableCalculations:i[1].dimensions}}),e.$on("updateCalculations",i[4]),t=new _t({props:{title:"but only if",placeholder:"add a filter...",availableDimensions:i[1].dimensions}}),t.$on("updateFilters",i[5]),{c(){I(e.$$.fragment),l=R(),I(t.$$.fragment)},m(s,r){A(e,s,r),k(s,l,r),A(t,s,r),n=!0},p(s,r){const c={};r&2&&(c.availableCalculations=s[1].dimensions),e.$set(c);const a={};r&2&&(a.availableDimensions=s[1].dimensions),t.$set(a)},i(s){n||(g(e.$$.fragment,s),g(t.$$.fragment,s),n=!0)},o(s){v(e.$$.fragment,s),v(t.$$.fragment,s),n=!1},d(s){F(e,s),s&&y(l),F(t,s)}}}function De(i){let e,l;return e=new Lt({props:{queryResult:i[2]}}),{c(){I(e.$$.fragment)},m(t,n){A(e,t,n),l=!0},p(t,n){const s={};n&4&&(s.queryResult=t[2]),e.$set(s)},i(t){l||(g(e.$$.fragment,t),l=!0)},o(t){v(e.$$.fragment,t),l=!1},d(t){F(e,t)}}}function jt(i){let e,l,t,n,s;l=new oe({props:{title:"Show me",placeholder:"find a metric...",availableCalculations:i[1].measures}}),l.$on("updateCalculations",i[3]);let r=i[0].length>0&&Re(i),c=i[2]!==null&&De(i);return{c(){e=b("div"),I(l.$$.fragment),t=R(),r&&r.c(),n=R(),c&&c.c()},m(a,o){k(a,e,o),A(l,e,null),p(e,t),r&&r.m(e,null),p(e,n),c&&c.m(e,null),s=!0},p(a,[o]){const f={};o&2&&(f.availableCalculations=a[1].measures),l.$set(f),a[0].length>0?r?(r.p(a,o),o&1&&g(r,1)):(r=Re(a),r.c(),g(r,1),r.m(e,n)):r&&(E(),v(r,1,1,()=>{r=null}),$()),a[2]!==null?c?(c.p(a,o),o&4&&g(c,1)):(c=De(a),c.c(),g(c,1),c.m(e,null)):c&&(E(),v(c,1,1,()=>{c=null}),$())},i(a){s||(g(l.$$.fragment,a),g(r),g(c),s=!0)},o(a){v(l.$$.fragment,a),v(r),v(c),s=!1},d(a){a&&y(e),F(l),r&&r.d(),c&&c.d()}}}function Nt(i,e,l){let t,n={measures:[],dimensions:[]},s=[],r=[],c=[],a=null;const o=h=>{l(0,s=h.detail.calculations),s.length===0&&(l(6,r=[]),l(2,a=null),m())},f=h=>{l(6,r=h.detail.calculations)},u=h=>{l(7,c=h.detail)},d=h=>{s.length>0&&fetch("/api/query/",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(h)}).then(_=>_.json()).then(_=>{l(2,a=_),l(1,n=_.metadata.store)})},m=()=>{fetch("/api/store/").then(h=>h.json()).then(h=>l(1,n=h)).catch(h=>console.error(h))};return m(),i.$$.update=()=>{i.$$.dirty&193&&l(8,t={measures:s.map(h=>h.id),dimensions:r.map(h=>h.id),filters:c}),i.$$.dirty&256&&d(t)},[s,n,a,o,f,u,r,c,t]}class Ot extends D{constructor(e){super();S(this,e,Nt,jt,L,{})}}function Tt(i){let e,l,t;return l=new Ot({}),{c(){e=b("div"),I(l.$$.fragment),w(e,"class","container svelte-t5466c")},m(n,s){k(n,e,s),A(l,e,null),t=!0},p:O,i(n){t||(g(l.$$.fragment,n),t=!0)},o(n){v(l.$$.fragment,n),t=!1},d(n){n&&y(e),F(l)}}}class Bt extends D{constructor(e){super();S(this,e,null,Tt,L,{})}}function Et(i){let e,l;return e=new Bt({}),{c(){I(e.$$.fragment)},m(t,n){A(e,t,n),l=!0},p:O,i(t){l||(g(e.$$.fragment,t),l=!0)},o(t){v(e.$$.fragment,t),l=!1},d(t){F(e,t)}}}class $t extends D{constructor(e){super();S(this,e,null,Et,L,{})}}new $t({target:document.body});