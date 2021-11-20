import { S as Q, i as S, s as B, e as _, t as O, a as R, b as p, c as w, d as f, f as M, n as P, g as L, h as T, m as j, j as b, k as q, l as A, o as D, p as E, q as F, u as H, r as I, v as $, w as J, x as C, y as x } from "./vendor.6a7c4d5c.js";
const ee = function() { const e = document.createElement("link").relList; if (e && e.supports && e.supports("modulepreload")) return; for (const n of document.querySelectorAll('link[rel="modulepreload"]')) l(n);
    new MutationObserver(n => { for (const r of n)
            if (r.type === "childList")
                for (const a of r.addedNodes) a.tagName === "LINK" && a.rel === "modulepreload" && l(a) }).observe(document, { childList: !0, subtree: !0 });

    function t(n) { const r = {}; return n.integrity && (r.integrity = n.integrity), n.referrerpolicy && (r.referrerPolicy = n.referrerpolicy), n.crossorigin === "use-credentials" ? r.credentials = "include" : n.crossorigin === "anonymous" ? r.credentials = "omit" : r.credentials = "same-origin", r }

    function l(n) { if (n.ep) return;
        n.ep = !0; const r = t(n);
        fetch(n.href, r) } };
ee();

function te(s) { let e, t, l, n, r, a; return { c() { e = _("div"), t = _("h1"), l = O(s[0]), n = R(), r = _("span"), a = O(s[1]), p(t, "class", "svelte-mi0gkn"), p(r, "class", "svelte-mi0gkn"), p(e, "class", "svelte-mi0gkn") }, m(i, u) { w(i, e, u), f(e, t), f(t, l), f(e, n), f(e, r), f(r, a) }, p(i, [u]) { u & 1 && M(l, i[0]), u & 2 && M(a, i[1]) }, i: P, o: P, d(i) { i && L(e) } } }

function le(s, e, t) { let l, { name: n } = e,
        { value: r } = e,
        { format: a = null } = e; return s.$$set = i => { "name" in i && t(0, n = i.name), "value" in i && t(2, r = i.value), "format" in i && t(3, a = i.format) }, s.$$.update = () => { s.$$.dirty & 12 && t(1, l = r) }, [n, l, r, a] }
class ne extends Q { constructor(e) { super();
        S(this, e, le, te, B, { name: 0, value: 2, format: 3 }) } }

function K(s, e, t) { const l = s.slice(); return l[3] = e[t].name, l[4] = e[t].value, l }

function V(s) { let e, t; return e = new ne({ props: { name: s[3], value: s[4] } }), { c() { T(e.$$.fragment) }, m(l, n) { j(e, l, n), t = !0 }, p(l, n) { const r = {};
            n & 1 && (r.name = l[3]), n & 1 && (r.value = l[4]), e.$set(r) }, i(l) { t || (b(e.$$.fragment, l), t = !0) }, o(l) { q(e.$$.fragment, l), t = !1 }, d(l) { A(e, l) } } }

function re(s) { let e, t, l = s[0],
        n = []; for (let a = 0; a < l.length; a += 1) n[a] = V(K(s, l, a)); const r = a => q(n[a], 1, 1, () => { n[a] = null }); return { c() { e = _("div"); for (let a = 0; a < n.length; a += 1) n[a].c();
            p(e, "class", "big-numbers svelte-s599iq") }, m(a, i) { w(a, e, i); for (let u = 0; u < n.length; u += 1) n[u].m(e, null);
            t = !0 }, p(a, [i]) { if (i & 1) { l = a[0]; let u; for (u = 0; u < l.length; u += 1) { const o = K(a, l, u);
                    n[u] ? (n[u].p(o, i), b(n[u], 1)) : (n[u] = V(o), n[u].c(), b(n[u], 1), n[u].m(e, null)) } for (D(), u = l.length; u < n.length; u += 1) r(u);
                E() } }, i(a) { if (!t) { for (let i = 0; i < l.length; i += 1) b(n[i]);
                t = !0 } }, o(a) { n = n.filter(Boolean); for (let i = 0; i < n.length; i += 1) q(n[i]);
            t = !1 }, d(a) { a && L(e), F(n, a) } } }

function ae(s, e, t) { let l, { data: n } = e,
        { meta: r } = e; return s.$$set = a => { "data" in a && t(1, n = a.data), "meta" in a && t(2, r = a.meta) }, s.$$.update = () => { s.$$.dirty & 6 && t(0, l = r.map(({ id: a, name: i }) => ({ name: i, value: n[a] }))) }, [l, n, r] }
class se extends Q { constructor(e) { super();
        S(this, e, ae, re, B, { data: 1, meta: 2 }) } }

function z(s, e, t) { const l = s.slice(); return l[4] = e[t], l }

function G(s, e, t) { const l = s.slice(); return l[7] = e[t], l }

function U(s, e, t) { const l = s.slice(); return l[10] = e[t], l }

function W(s, e) { let t, l = e[10] + "",
        n; return { key: s, first: null, c() { t = _("th"), n = O(l), p(t, "class", "svelte-10mmylh"), this.first = t }, m(r, a) { w(r, t, a), f(t, n) }, p(r, a) { e = r, a & 2 && l !== (l = e[10] + "") && M(n, l) }, d(r) { r && L(t) } } }

function X(s, e) { let t, l = e[4][e[7]] + "",
        n; return { key: s, first: null, c() { t = _("td"), n = O(l), p(t, "class", "svelte-10mmylh"), this.first = t }, m(r, a) { w(r, t, a), f(t, n) }, p(r, a) { e = r, a & 5 && l !== (l = e[4][e[7]] + "") && M(n, l) }, d(r) { r && L(t) } } }

function Y(s) { let e, t = [],
        l = new Map,
        n, r = s[2]; const a = i => i[7]; for (let i = 0; i < r.length; i += 1) { let u = G(s, r, i),
            o = a(u);
        l.set(o, t[i] = X(o, u)) } return { c() { e = _("tr"); for (let i = 0; i < t.length; i += 1) t[i].c();
            n = R() }, m(i, u) { w(i, e, u); for (let o = 0; o < t.length; o += 1) t[o].m(e, null);
            f(e, n) }, p(i, u) { u & 5 && (r = i[2], t = H(t, u, a, 1, i, r, l, e, I, X, n, G)) }, d(i) { i && L(e); for (let u = 0; u < t.length; u += 1) t[u].d() } } }

function ie(s) { let e, t, l, n, r = [],
        a = new Map,
        i, u, o = s[1]; const v = c => c[10]; for (let c = 0; c < o.length; c += 1) { let d = U(s, o, c),
            m = v(d);
        a.set(m, r[c] = W(m, d)) } let k = s[0],
        h = []; for (let c = 0; c < k.length; c += 1) h[c] = Y(z(s, k, c)); return { c() { e = _("div"), t = _("table"), l = _("thead"), n = _("tr"); for (let c = 0; c < r.length; c += 1) r[c].c();
            i = R(), u = _("tbody"); for (let c = 0; c < h.length; c += 1) h[c].c();
            p(t, "class", "svelte-10mmylh"), p(e, "class", "table-wrapper svelte-10mmylh") }, m(c, d) { w(c, e, d), f(e, t), f(t, l), f(l, n); for (let m = 0; m < r.length; m += 1) r[m].m(n, null);
            f(t, i), f(t, u); for (let m = 0; m < h.length; m += 1) h[m].m(u, null) }, p(c, [d]) { if (d & 2 && (o = c[1], r = H(r, d, v, 1, c, o, a, n, I, W, null, U)), d & 5) { k = c[0]; let m; for (m = 0; m < k.length; m += 1) { const g = z(c, k, m);
                    h[m] ? h[m].p(g, d) : (h[m] = Y(g), h[m].c(), h[m].m(u, null)) } for (; m < h.length; m += 1) h[m].d(1);
                h.length = k.length } }, i: P, o: P, d(c) { c && L(e); for (let d = 0; d < r.length; d += 1) r[d].d();
            F(h, c) } } }

function ue(s, e, t) { let l, n, { data: r } = e,
        { meta: a } = e; return s.$$set = i => { "data" in i && t(0, r = i.data), "meta" in i && t(3, a = i.meta) }, s.$$.update = () => { s.$$.dirty & 8 && t(2, l = a.map(i => i.id)), s.$$.dirty & 8 && t(1, n = a.map(i => i.name)) }, [r, n, l, a] }
class ce extends Q { constructor(e) { super();
        S(this, e, ue, ie, B, { data: 0, meta: 3 }) } }

function oe(s) { let e, t; return e = new ce({ props: { data: s[2], meta: s[1] } }), { c() { T(e.$$.fragment) }, m(l, n) { j(e, l, n), t = !0 }, p(l, n) { const r = {};
            n & 4 && (r.data = l[2]), n & 2 && (r.meta = l[1]), e.$set(r) }, i(l) { t || (b(e.$$.fragment, l), t = !0) }, o(l) { q(e.$$.fragment, l), t = !1 }, d(l) { A(e, l) } } }

function fe(s) { let e, t; return e = new se({ props: { data: s[2][0], meta: s[1] } }), { c() { T(e.$$.fragment) }, m(l, n) { j(e, l, n), t = !0 }, p(l, n) { const r = {};
            n & 4 && (r.data = l[2][0]), n & 2 && (r.meta = l[1]), e.$set(r) }, i(l) { t || (b(e.$$.fragment, l), t = !0) }, o(l) { q(e.$$.fragment, l), t = !1 }, d(l) { A(e, l) } } }

function me(s) { let e, t, l, n; const r = [fe, oe],
        a = [];

    function i(u, o) { return u[0].data.length === 1 ? 0 : u[0].data.length > 1 ? 1 : -1 } return ~(e = i(s)) && (t = a[e] = r[e](s)), { c() { t && t.c(), l = $() }, m(u, o) {~e && a[e].m(u, o), w(u, l, o), n = !0 }, p(u, [o]) { let v = e;
            e = i(u), e === v ? ~e && a[e].p(u, o) : (t && (D(), q(a[v], 1, 1, () => { a[v] = null }), E()), ~e ? (t = a[e], t ? t.p(u, o) : (t = a[e] = r[e](u), t.c()), b(t, 1), t.m(l.parentNode, l)) : t = null) }, i(u) { n || (b(t), n = !0) }, o(u) { q(t), n = !1 }, d(u) {~e && a[e].d(u), u && L(l) } } }

function de(s, e, t) { let l, n, { queryResult: r } = e; return s.$$set = a => { "queryResult" in a && t(0, r = a.queryResult) }, s.$$.update = () => { s.$$.dirty & 1 && t(2, l = r.data), s.$$.dirty & 1 && t(1, n = r.metadata.columns) }, [r, n, l] }
class _e extends Q { constructor(e) { super();
        S(this, e, de, me, B, { queryResult: 0 }) } }
class he { request(e, t) { return fetch("/graphql/", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query: e, variables: t }) }).then(l => l.json()).then(l => l.data) } }

function Z(s) { let e, t; return e = new _e({ props: { queryResult: s[0] } }), { c() { T(e.$$.fragment) }, m(l, n) { j(e, l, n), t = !0 }, p(l, n) { const r = {};
            n & 1 && (r.queryResult = l[0]), e.$set(r) }, i(l) { t || (b(e.$$.fragment, l), t = !0) }, o(l) { q(e.$$.fragment, l), t = !1 }, d(l) { A(e, l) } } }

function ge(s) { let e, t, l, n, r, a, i, u, o, v, k, h, c, d, m, g = s[0] !== null && Z(s); return { c() { e = _("div"), t = _("div"), l = _("textarea"), n = R(), r = _("button"), a = O(s[4]), i = R(), u = _("label"), o = _("input"), v = O(" Formatting"), k = R(), h = _("div"), g && g.c(), p(l, "id", "query"), p(l, "spellcheck", "false"), p(l, "class", "svelte-1rd28rf"), r.disabled = s[1], p(o, "type", "checkbox"), p(t, "class", "query card metric"), p(h, "class", "card display svelte-1rd28rf"), p(e, "class", "wrapper svelte-1rd28rf") }, m(y, N) { w(y, e, N), f(e, t), f(t, l), J(l, s[2]), f(t, n), f(t, r), f(r, a), f(t, i), f(t, u), f(u, o), o.checked = s[3], f(u, v), f(e, k), f(e, h), g && g.m(h, null), c = !0, d || (m = [C(l, "input", s[7]), C(l, "keydown", s[6]), C(r, "click", s[5]), C(o, "change", s[8])], d = !0) }, p(y, [N]) { N & 4 && J(l, y[2]), (!c || N & 16) && M(a, y[4]), (!c || N & 2) && (r.disabled = y[1]), N & 8 && (o.checked = y[3]), y[0] !== null ? g ? (g.p(y, N), N & 1 && b(g, 1)) : (g = Z(y), g.c(), b(g, 1), g.m(h, null)) : g && (D(), q(g, 1, 1, () => { g = null }), E()) }, i(y) { c || (b(g), c = !0) }, o(y) { q(g), c = !1 }, d(y) { y && L(e), g && g.d(), d = !1, x(m) } } }

function pe(s, e, t) { let l, n = "",
        r = null,
        a = !1,
        i = !0; const u = `
    query executeQuery($query: String!, $formatting: Boolean!) {
        result: qlQuery(input: $query, formatting: $formatting) {
            metadata {
                rawQuery
                columns {
                    id
                    name
                }
            }
            data
        }
    }
    `,
        o = new he;

    function v() { t(1, a = !0), o.request(u, { query: n, formatting: i }).then(d => { t(0, r = d.result), t(1, a = !1) }).catch(d => { console.log(d), t(1, a = !1) }) }

    function k(d) { d.key == "Enter" && d.getModifierState("Control") && v() }

    function h() { n = this.value, t(2, n) }

    function c() { i = this.checked, t(3, i) } return s.$$.update = () => { s.$$.dirty & 2 && t(4, l = a ? "Running..." : "Execute"), s.$$.dirty & 1 && r !== null && console.log(r.metadata.rawQuery) }, [r, a, n, i, l, v, k, h, c] }
class ye extends Q { constructor(e) { super();
        S(this, e, pe, ge, B, {}) } }

function be(s) { let e, t, l, n, r, a, i; return a = new ye({}), { c() { e = _("div"), t = _("nav"), t.innerHTML = '<div class="container">Dictum</div>', l = R(), n = _("div"), r = _("div"), T(a.$$.fragment), p(t, "class", "navbar svelte-bhc2bh"), p(r, "class", "container"), p(n, "class", "page svelte-bhc2bh") }, m(u, o) { w(u, e, o), f(e, t), f(e, l), f(e, n), f(n, r), j(a, r, null), i = !0 }, p: P, i(u) { i || (b(a.$$.fragment, u), i = !0) }, o(u) { q(a.$$.fragment, u), i = !1 }, d(u) { u && L(e), A(a) } } }
class ve extends Q { constructor(e) { super();
        S(this, e, null, be, B, {}) } }
new ve({ target: document.body });