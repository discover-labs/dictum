function A(){}function z(t){return t&&typeof t=="object"&&typeof t.then=="function"}function C(t){return t()}function S(){return Object.create(null)}function p(t){t.forEach(C)}function B(t){return typeof t=="function"}function V(t,e){return t!=t?e==e:t!==e||t&&typeof t=="object"||typeof t=="function"}function F(t){return Object.keys(t).length===0}function W(t,e){t.appendChild(e)}function X(t,e,n){t.insertBefore(e,n||null)}function M(t){t.parentNode.removeChild(t)}function Y(t,e){for(let n=0;n<t.length;n+=1)t[n]&&t[n].d(e)}function Z(t){return document.createElement(t)}function P(t){return document.createTextNode(t)}function tt(){return P(" ")}function et(t,e,n){n==null?t.removeAttribute(e):t.getAttribute(e)!==n&&t.setAttribute(e,n)}function q(t){return Array.from(t.childNodes)}function nt(t,e){e=""+e,t.wholeText!==e&&(t.data=e)}let g;function f(t){g=t}function D(){if(!g)throw new Error("Function called outside component initialization");return g}const m=[],N=[],b=[],O=[],G=Promise.resolve();let y=!1;function H(){y||(y=!0,G.then(E))}function k(t){b.push(t)}let x=!1;const w=new Set;function E(){if(!x){x=!0;do{for(let t=0;t<m.length;t+=1){const e=m[t];f(e),I(e.$$)}for(f(null),m.length=0;N.length;)N.pop()();for(let t=0;t<b.length;t+=1){const e=b[t];w.has(e)||(w.add(e),e())}b.length=0}while(m.length);for(;O.length;)O.pop()();y=!1,x=!1,w.clear()}}function I(t){if(t.fragment!==null){t.update(),p(t.before_update);const e=t.dirty;t.dirty=[-1],t.fragment&&t.fragment.p(t.ctx,e),t.after_update.forEach(k)}}const $=new Set;let i;function J(){i={r:0,c:[],p:i}}function K(){i.r||p(i.c),i=i.p}function T(t,e){t&&t.i&&($.delete(t),t.i(e))}function L(t,e,n,c){if(t&&t.o){if($.has(t))return;$.add(t),i.c.push(()=>{$.delete(t),c&&(n&&t.d(1),c())}),t.o(e)}}function rt(t,e){const n=e.token={};function c(u,l,a,d){if(e.token!==n)return;e.resolved=d;let s=e.ctx;a!==void 0&&(s=s.slice(),s[a]=d);const r=u&&(e.current=u)(s);let _=!1;e.block&&(e.blocks?e.blocks.forEach((o,h)=>{h!==l&&o&&(J(),L(o,1,1,()=>{e.blocks[h]===o&&(e.blocks[h]=null)}),K())}):e.block.d(1),r.c(),T(r,1),r.m(e.mount(),e.anchor),_=!0),e.block=r,e.blocks&&(e.blocks[l]=r),_&&E()}if(z(t)){const u=D();if(t.then(l=>{f(u),c(e.then,1,e.value,l),f(null)},l=>{if(f(u),c(e.catch,2,e.error,l),f(null),!e.hasCatch)throw l}),e.current!==e.pending)return c(e.pending,0),!0}else{if(e.current!==e.then)return c(e.then,1,e.value,t),!0;e.resolved=t}}function ct(t,e,n){const c=e.slice(),{resolved:u}=t;t.current===t.then&&(c[t.value]=u),t.current===t.catch&&(c[t.error]=u),t.block.p(c,n)}function ut(t){t&&t.c()}function Q(t,e,n,c){const{fragment:u,on_mount:l,on_destroy:a,after_update:d}=t.$$;u&&u.m(e,n),c||k(()=>{const s=l.map(C).filter(B);a?a.push(...s):p(s),t.$$.on_mount=[]}),d.forEach(k)}function R(t,e){const n=t.$$;n.fragment!==null&&(p(n.on_destroy),n.fragment&&n.fragment.d(e),n.on_destroy=n.fragment=null,n.ctx=[])}function U(t,e){t.$$.dirty[0]===-1&&(m.push(t),H(),t.$$.dirty.fill(0)),t.$$.dirty[e/31|0]|=1<<e%31}function st(t,e,n,c,u,l,a,d=[-1]){const s=g;f(t);const r=t.$$={fragment:null,ctx:null,props:l,update:A,not_equal:u,bound:S(),on_mount:[],on_destroy:[],on_disconnect:[],before_update:[],after_update:[],context:new Map(e.context||(s?s.$$.context:[])),callbacks:S(),dirty:d,skip_bound:!1,root:e.target||s.$$.root};a&&a(r.root);let _=!1;if(r.ctx=n?n(t,e.props||{},(o,h,...v)=>{const j=v.length?v[0]:h;return r.ctx&&u(r.ctx[o],r.ctx[o]=j)&&(!r.skip_bound&&r.bound[o]&&r.bound[o](j),_&&U(t,o)),h}):[],r.update(),_=!0,p(r.before_update),r.fragment=c?c(r.ctx):!1,e.target){if(e.hydrate){const o=q(e.target);r.fragment&&r.fragment.l(o),o.forEach(M)}else r.fragment&&r.fragment.c();e.intro&&T(t.$$.fragment),Q(t,e.target,e.anchor,e.customElement),E()}f(s)}class ot{$destroy(){R(this,1),this.$destroy=A}$on(e,n){const c=this.$$.callbacks[e]||(this.$$.callbacks[e]=[]);return c.push(n),()=>{const u=c.indexOf(n);u!==-1&&c.splice(u,1)}}$set(e){this.$$set&&!F(e)&&(this.$$.skip_bound=!0,this.$$set(e),this.$$.skip_bound=!1)}}export{ot as S,X as a,W as b,nt as c,M as d,Z as e,tt as f,et as g,Y as h,st as i,rt as j,T as k,L as l,ut as m,A as n,Q as o,R as p,V as s,P as t,ct as u};
