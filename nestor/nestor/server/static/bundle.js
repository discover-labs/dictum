
(function(l, r) { if (!l || l.getElementById('livereloadscript')) return; r = l.createElement('script'); r.async = 1; r.src = '//' + (self.location.host || 'localhost').split(':')[0] + ':35730/livereload.js?snipver=1'; r.id = 'livereloadscript'; l.getElementsByTagName('head')[0].appendChild(r) })(self.document);
var app = (function () {
    'use strict';

    function noop() { }
    function add_location(element, file, line, column, char) {
        element.__svelte_meta = {
            loc: { file, line, column, char }
        };
    }
    function run(fn) {
        return fn();
    }
    function blank_object() {
        return Object.create(null);
    }
    function run_all(fns) {
        fns.forEach(run);
    }
    function is_function(thing) {
        return typeof thing === 'function';
    }
    function safe_not_equal(a, b) {
        return a != a ? b == b : a !== b || ((a && typeof a === 'object') || typeof a === 'function');
    }
    function is_empty(obj) {
        return Object.keys(obj).length === 0;
    }
    function append(target, node) {
        target.appendChild(node);
    }
    function insert(target, node, anchor) {
        target.insertBefore(node, anchor || null);
    }
    function detach(node) {
        node.parentNode.removeChild(node);
    }
    function destroy_each(iterations, detaching) {
        for (let i = 0; i < iterations.length; i += 1) {
            if (iterations[i])
                iterations[i].d(detaching);
        }
    }
    function element(name) {
        return document.createElement(name);
    }
    function text(data) {
        return document.createTextNode(data);
    }
    function space() {
        return text(' ');
    }
    function empty() {
        return text('');
    }
    function listen(node, event, handler, options) {
        node.addEventListener(event, handler, options);
        return () => node.removeEventListener(event, handler, options);
    }
    function attr(node, attribute, value) {
        if (value == null)
            node.removeAttribute(attribute);
        else if (node.getAttribute(attribute) !== value)
            node.setAttribute(attribute, value);
    }
    function children(element) {
        return Array.from(element.childNodes);
    }
    function set_input_value(input, value) {
        input.value = value == null ? '' : value;
    }
    function toggle_class(element, name, toggle) {
        element.classList[toggle ? 'add' : 'remove'](name);
    }
    function custom_event(type, detail, bubbles = false) {
        const e = document.createEvent('CustomEvent');
        e.initCustomEvent(type, bubbles, false, detail);
        return e;
    }

    let current_component;
    function set_current_component(component) {
        current_component = component;
    }
    function get_current_component() {
        if (!current_component)
            throw new Error('Function called outside component initialization');
        return current_component;
    }
    function createEventDispatcher() {
        const component = get_current_component();
        return (type, detail) => {
            const callbacks = component.$$.callbacks[type];
            if (callbacks) {
                // TODO are there situations where events could be dispatched
                // in a server (non-DOM) environment?
                const event = custom_event(type, detail);
                callbacks.slice().forEach(fn => {
                    fn.call(component, event);
                });
            }
        };
    }

    const dirty_components = [];
    const binding_callbacks = [];
    const render_callbacks = [];
    const flush_callbacks = [];
    const resolved_promise = Promise.resolve();
    let update_scheduled = false;
    function schedule_update() {
        if (!update_scheduled) {
            update_scheduled = true;
            resolved_promise.then(flush);
        }
    }
    function add_render_callback(fn) {
        render_callbacks.push(fn);
    }
    let flushing = false;
    const seen_callbacks = new Set();
    function flush() {
        if (flushing)
            return;
        flushing = true;
        do {
            // first, call beforeUpdate functions
            // and update components
            for (let i = 0; i < dirty_components.length; i += 1) {
                const component = dirty_components[i];
                set_current_component(component);
                update(component.$$);
            }
            set_current_component(null);
            dirty_components.length = 0;
            while (binding_callbacks.length)
                binding_callbacks.pop()();
            // then, once components are updated, call
            // afterUpdate functions. This may cause
            // subsequent updates...
            for (let i = 0; i < render_callbacks.length; i += 1) {
                const callback = render_callbacks[i];
                if (!seen_callbacks.has(callback)) {
                    // ...so guard against infinite loops
                    seen_callbacks.add(callback);
                    callback();
                }
            }
            render_callbacks.length = 0;
        } while (dirty_components.length);
        while (flush_callbacks.length) {
            flush_callbacks.pop()();
        }
        update_scheduled = false;
        flushing = false;
        seen_callbacks.clear();
    }
    function update($$) {
        if ($$.fragment !== null) {
            $$.update();
            run_all($$.before_update);
            const dirty = $$.dirty;
            $$.dirty = [-1];
            $$.fragment && $$.fragment.p($$.ctx, dirty);
            $$.after_update.forEach(add_render_callback);
        }
    }
    const outroing = new Set();
    let outros;
    function group_outros() {
        outros = {
            r: 0,
            c: [],
            p: outros // parent group
        };
    }
    function check_outros() {
        if (!outros.r) {
            run_all(outros.c);
        }
        outros = outros.p;
    }
    function transition_in(block, local) {
        if (block && block.i) {
            outroing.delete(block);
            block.i(local);
        }
    }
    function transition_out(block, local, detach, callback) {
        if (block && block.o) {
            if (outroing.has(block))
                return;
            outroing.add(block);
            outros.c.push(() => {
                outroing.delete(block);
                if (callback) {
                    if (detach)
                        block.d(1);
                    callback();
                }
            });
            block.o(local);
        }
    }

    const globals = (typeof window !== 'undefined'
        ? window
        : typeof globalThis !== 'undefined'
            ? globalThis
            : global);

    function destroy_block(block, lookup) {
        block.d(1);
        lookup.delete(block.key);
    }
    function outro_and_destroy_block(block, lookup) {
        transition_out(block, 1, 1, () => {
            lookup.delete(block.key);
        });
    }
    function update_keyed_each(old_blocks, dirty, get_key, dynamic, ctx, list, lookup, node, destroy, create_each_block, next, get_context) {
        let o = old_blocks.length;
        let n = list.length;
        let i = o;
        const old_indexes = {};
        while (i--)
            old_indexes[old_blocks[i].key] = i;
        const new_blocks = [];
        const new_lookup = new Map();
        const deltas = new Map();
        i = n;
        while (i--) {
            const child_ctx = get_context(ctx, list, i);
            const key = get_key(child_ctx);
            let block = lookup.get(key);
            if (!block) {
                block = create_each_block(key, child_ctx);
                block.c();
            }
            else if (dynamic) {
                block.p(child_ctx, dirty);
            }
            new_lookup.set(key, new_blocks[i] = block);
            if (key in old_indexes)
                deltas.set(key, Math.abs(i - old_indexes[key]));
        }
        const will_move = new Set();
        const did_move = new Set();
        function insert(block) {
            transition_in(block, 1);
            block.m(node, next);
            lookup.set(block.key, block);
            next = block.first;
            n--;
        }
        while (o && n) {
            const new_block = new_blocks[n - 1];
            const old_block = old_blocks[o - 1];
            const new_key = new_block.key;
            const old_key = old_block.key;
            if (new_block === old_block) {
                // do nothing
                next = new_block.first;
                o--;
                n--;
            }
            else if (!new_lookup.has(old_key)) {
                // remove old block
                destroy(old_block, lookup);
                o--;
            }
            else if (!lookup.has(new_key) || will_move.has(new_key)) {
                insert(new_block);
            }
            else if (did_move.has(old_key)) {
                o--;
            }
            else if (deltas.get(new_key) > deltas.get(old_key)) {
                did_move.add(new_key);
                insert(new_block);
            }
            else {
                will_move.add(old_key);
                o--;
            }
        }
        while (o--) {
            const old_block = old_blocks[o];
            if (!new_lookup.has(old_block.key))
                destroy(old_block, lookup);
        }
        while (n)
            insert(new_blocks[n - 1]);
        return new_blocks;
    }
    function validate_each_keys(ctx, list, get_context, get_key) {
        const keys = new Set();
        for (let i = 0; i < list.length; i++) {
            const key = get_key(get_context(ctx, list, i));
            if (keys.has(key)) {
                throw new Error('Cannot have duplicate keys in a keyed each');
            }
            keys.add(key);
        }
    }
    function create_component(block) {
        block && block.c();
    }
    function mount_component(component, target, anchor, customElement) {
        const { fragment, on_mount, on_destroy, after_update } = component.$$;
        fragment && fragment.m(target, anchor);
        if (!customElement) {
            // onMount happens before the initial afterUpdate
            add_render_callback(() => {
                const new_on_destroy = on_mount.map(run).filter(is_function);
                if (on_destroy) {
                    on_destroy.push(...new_on_destroy);
                }
                else {
                    // Edge case - component was destroyed immediately,
                    // most likely as a result of a binding initialising
                    run_all(new_on_destroy);
                }
                component.$$.on_mount = [];
            });
        }
        after_update.forEach(add_render_callback);
    }
    function destroy_component(component, detaching) {
        const $$ = component.$$;
        if ($$.fragment !== null) {
            run_all($$.on_destroy);
            $$.fragment && $$.fragment.d(detaching);
            // TODO null out other refs, including component.$$ (but need to
            // preserve final state?)
            $$.on_destroy = $$.fragment = null;
            $$.ctx = [];
        }
    }
    function make_dirty(component, i) {
        if (component.$$.dirty[0] === -1) {
            dirty_components.push(component);
            schedule_update();
            component.$$.dirty.fill(0);
        }
        component.$$.dirty[(i / 31) | 0] |= (1 << (i % 31));
    }
    function init(component, options, instance, create_fragment, not_equal, props, append_styles, dirty = [-1]) {
        const parent_component = current_component;
        set_current_component(component);
        const $$ = component.$$ = {
            fragment: null,
            ctx: null,
            // state
            props,
            update: noop,
            not_equal,
            bound: blank_object(),
            // lifecycle
            on_mount: [],
            on_destroy: [],
            on_disconnect: [],
            before_update: [],
            after_update: [],
            context: new Map(options.context || (parent_component ? parent_component.$$.context : [])),
            // everything else
            callbacks: blank_object(),
            dirty,
            skip_bound: false,
            root: options.target || parent_component.$$.root
        };
        append_styles && append_styles($$.root);
        let ready = false;
        $$.ctx = instance
            ? instance(component, options.props || {}, (i, ret, ...rest) => {
                const value = rest.length ? rest[0] : ret;
                if ($$.ctx && not_equal($$.ctx[i], $$.ctx[i] = value)) {
                    if (!$$.skip_bound && $$.bound[i])
                        $$.bound[i](value);
                    if (ready)
                        make_dirty(component, i);
                }
                return ret;
            })
            : [];
        $$.update();
        ready = true;
        run_all($$.before_update);
        // `false` as a special case of no DOM component
        $$.fragment = create_fragment ? create_fragment($$.ctx) : false;
        if (options.target) {
            if (options.hydrate) {
                const nodes = children(options.target);
                // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
                $$.fragment && $$.fragment.l(nodes);
                nodes.forEach(detach);
            }
            else {
                // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
                $$.fragment && $$.fragment.c();
            }
            if (options.intro)
                transition_in(component.$$.fragment);
            mount_component(component, options.target, options.anchor, options.customElement);
            flush();
        }
        set_current_component(parent_component);
    }
    /**
     * Base class for Svelte components. Used when dev=false.
     */
    class SvelteComponent {
        $destroy() {
            destroy_component(this, 1);
            this.$destroy = noop;
        }
        $on(type, callback) {
            const callbacks = (this.$$.callbacks[type] || (this.$$.callbacks[type] = []));
            callbacks.push(callback);
            return () => {
                const index = callbacks.indexOf(callback);
                if (index !== -1)
                    callbacks.splice(index, 1);
            };
        }
        $set($$props) {
            if (this.$$set && !is_empty($$props)) {
                this.$$.skip_bound = true;
                this.$$set($$props);
                this.$$.skip_bound = false;
            }
        }
    }

    function dispatch_dev(type, detail) {
        document.dispatchEvent(custom_event(type, Object.assign({ version: '3.43.1' }, detail), true));
    }
    function append_dev(target, node) {
        dispatch_dev('SvelteDOMInsert', { target, node });
        append(target, node);
    }
    function insert_dev(target, node, anchor) {
        dispatch_dev('SvelteDOMInsert', { target, node, anchor });
        insert(target, node, anchor);
    }
    function detach_dev(node) {
        dispatch_dev('SvelteDOMRemove', { node });
        detach(node);
    }
    function listen_dev(node, event, handler, options, has_prevent_default, has_stop_propagation) {
        const modifiers = options === true ? ['capture'] : options ? Array.from(Object.keys(options)) : [];
        if (has_prevent_default)
            modifiers.push('preventDefault');
        if (has_stop_propagation)
            modifiers.push('stopPropagation');
        dispatch_dev('SvelteDOMAddEventListener', { node, event, handler, modifiers });
        const dispose = listen(node, event, handler, options);
        return () => {
            dispatch_dev('SvelteDOMRemoveEventListener', { node, event, handler, modifiers });
            dispose();
        };
    }
    function attr_dev(node, attribute, value) {
        attr(node, attribute, value);
        if (value == null)
            dispatch_dev('SvelteDOMRemoveAttribute', { node, attribute });
        else
            dispatch_dev('SvelteDOMSetAttribute', { node, attribute, value });
    }
    function set_data_dev(text, data) {
        data = '' + data;
        if (text.wholeText === data)
            return;
        dispatch_dev('SvelteDOMSetData', { node: text, data });
        text.data = data;
    }
    function validate_each_argument(arg) {
        if (typeof arg !== 'string' && !(arg && typeof arg === 'object' && 'length' in arg)) {
            let msg = '{#each} only iterates over array-like objects.';
            if (typeof Symbol === 'function' && arg && Symbol.iterator in arg) {
                msg += ' You can use a spread to convert this iterable into an array.';
            }
            throw new Error(msg);
        }
    }
    function validate_slots(name, slot, keys) {
        for (const slot_key of Object.keys(slot)) {
            if (!~keys.indexOf(slot_key)) {
                console.warn(`<${name}> received an unexpected slot "${slot_key}".`);
            }
        }
    }
    /**
     * Base class for Svelte components with some minor dev-enhancements. Used when dev=true.
     */
    class SvelteComponentDev extends SvelteComponent {
        constructor(options) {
            if (!options || (!options.target && !options.$$inline)) {
                throw new Error("'target' is a required option");
            }
            super();
        }
        $destroy() {
            super.$destroy();
            this.$destroy = () => {
                console.warn('Component was already destroyed'); // eslint-disable-line no-console
            };
        }
        $capture_state() { }
        $inject_state() { }
    }

    /* src/components/builder/CalculationDisplay.svelte generated by Svelte v3.43.1 */
    const file$9 = "src/components/builder/CalculationDisplay.svelte";

    function create_fragment$b(ctx) {
    	let div;
    	let mark;
    	let span;
    	let t0;
    	let t1;
    	let t2;
    	let t3;
    	let button;
    	let mounted;
    	let dispose;

    	const block = {
    		c: function create() {
    			div = element("div");
    			mark = element("mark");
    			span = element("span");
    			t0 = text(/*name*/ ctx[0]);
    			t1 = text(" (");
    			t2 = text(/*type*/ ctx[1]);
    			t3 = text(")");
    			button = element("button");
    			button.textContent = "x";
    			add_location(span, file$9, 11, 10, 281);
    			add_location(button, file$9, 11, 38, 309);
    			add_location(mark, file$9, 11, 4, 275);
    			attr_dev(div, "class", "calculation svelte-ws2txc");
    			add_location(div, file$9, 10, 0, 245);
    		},
    		l: function claim(nodes) {
    			throw new Error("options.hydrate only works if the component was compiled with the `hydratable: true` option");
    		},
    		m: function mount(target, anchor) {
    			insert_dev(target, div, anchor);
    			append_dev(div, mark);
    			append_dev(mark, span);
    			append_dev(span, t0);
    			append_dev(span, t1);
    			append_dev(span, t2);
    			append_dev(span, t3);
    			append_dev(mark, button);

    			if (!mounted) {
    				dispose = listen_dev(button, "click", /*close*/ ctx[2], false, false, false);
    				mounted = true;
    			}
    		},
    		p: function update(ctx, [dirty]) {
    			if (dirty & /*name*/ 1) set_data_dev(t0, /*name*/ ctx[0]);
    			if (dirty & /*type*/ 2) set_data_dev(t2, /*type*/ ctx[1]);
    		},
    		i: noop,
    		o: noop,
    		d: function destroy(detaching) {
    			if (detaching) detach_dev(div);
    			mounted = false;
    			dispose();
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_fragment$b.name,
    		type: "component",
    		source: "",
    		ctx
    	});

    	return block;
    }

    function instance$b($$self, $$props, $$invalidate) {
    	let { $$slots: slots = {}, $$scope } = $$props;
    	validate_slots('CalculationDisplay', slots, []);
    	let { id } = $$props;
    	let { name } = $$props;
    	let { type } = $$props;
    	const dispatch = createEventDispatcher();
    	const close = event => dispatch("closeItemClick", { id });
    	const writable_props = ['id', 'name', 'type'];

    	Object.keys($$props).forEach(key => {
    		if (!~writable_props.indexOf(key) && key.slice(0, 2) !== '$$' && key !== 'slot') console.warn(`<CalculationDisplay> was created with unknown prop '${key}'`);
    	});

    	$$self.$$set = $$props => {
    		if ('id' in $$props) $$invalidate(3, id = $$props.id);
    		if ('name' in $$props) $$invalidate(0, name = $$props.name);
    		if ('type' in $$props) $$invalidate(1, type = $$props.type);
    	};

    	$$self.$capture_state = () => ({
    		createEventDispatcher,
    		id,
    		name,
    		type,
    		dispatch,
    		close
    	});

    	$$self.$inject_state = $$props => {
    		if ('id' in $$props) $$invalidate(3, id = $$props.id);
    		if ('name' in $$props) $$invalidate(0, name = $$props.name);
    		if ('type' in $$props) $$invalidate(1, type = $$props.type);
    	};

    	if ($$props && "$$inject" in $$props) {
    		$$self.$inject_state($$props.$$inject);
    	}

    	return [name, type, close, id];
    }

    class CalculationDisplay extends SvelteComponentDev {
    	constructor(options) {
    		super(options);
    		init(this, options, instance$b, create_fragment$b, safe_not_equal, { id: 3, name: 0, type: 1 });

    		dispatch_dev("SvelteRegisterComponent", {
    			component: this,
    			tagName: "CalculationDisplay",
    			options,
    			id: create_fragment$b.name
    		});

    		const { ctx } = this.$$;
    		const props = options.props || {};

    		if (/*id*/ ctx[3] === undefined && !('id' in props)) {
    			console.warn("<CalculationDisplay> was created without expected prop 'id'");
    		}

    		if (/*name*/ ctx[0] === undefined && !('name' in props)) {
    			console.warn("<CalculationDisplay> was created without expected prop 'name'");
    		}

    		if (/*type*/ ctx[1] === undefined && !('type' in props)) {
    			console.warn("<CalculationDisplay> was created without expected prop 'type'");
    		}
    	}

    	get id() {
    		throw new Error("<CalculationDisplay>: Props cannot be read directly from the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}

    	set id(value) {
    		throw new Error("<CalculationDisplay>: Props cannot be set directly on the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}

    	get name() {
    		throw new Error("<CalculationDisplay>: Props cannot be read directly from the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}

    	set name(value) {
    		throw new Error("<CalculationDisplay>: Props cannot be set directly on the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}

    	get type() {
    		throw new Error("<CalculationDisplay>: Props cannot be read directly from the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}

    	set type(value) {
    		throw new Error("<CalculationDisplay>: Props cannot be set directly on the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}
    }

    /* src/components/builder/CalculationListItem.svelte generated by Svelte v3.43.1 */
    const file$8 = "src/components/builder/CalculationListItem.svelte";

    // (24:4) {#if description}
    function create_if_block$4(ctx) {
    	let p;
    	let t;

    	const block = {
    		c: function create() {
    			p = element("p");
    			t = text(/*description*/ ctx[1]);
    			attr_dev(p, "class", "description svelte-b1dmlw");
    			add_location(p, file$8, 24, 8, 550);
    		},
    		m: function mount(target, anchor) {
    			insert_dev(target, p, anchor);
    			append_dev(p, t);
    		},
    		p: function update(ctx, dirty) {
    			if (dirty & /*description*/ 2) set_data_dev(t, /*description*/ ctx[1]);
    		},
    		d: function destroy(detaching) {
    			if (detaching) detach_dev(p);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_if_block$4.name,
    		type: "if",
    		source: "(24:4) {#if description}",
    		ctx
    	});

    	return block;
    }

    function create_fragment$a(ctx) {
    	let div1;
    	let div0;
    	let span;
    	let t0;
    	let t1;
    	let mounted;
    	let dispose;
    	let if_block = /*description*/ ctx[1] && create_if_block$4(ctx);

    	const block = {
    		c: function create() {
    			div1 = element("div");
    			div0 = element("div");
    			span = element("span");
    			t0 = text(/*name*/ ctx[0]);
    			t1 = space();
    			if (if_block) if_block.c();
    			add_location(span, file$8, 21, 8, 489);
    			attr_dev(div0, "class", "header svelte-b1dmlw");
    			add_location(div0, file$8, 20, 4, 460);
    			attr_dev(div1, "class", "wrapper svelte-b1dmlw");
    			toggle_class(div1, "selected", /*selected*/ ctx[2]);
    			add_location(div1, file$8, 13, 0, 331);
    		},
    		l: function claim(nodes) {
    			throw new Error("options.hydrate only works if the component was compiled with the `hydratable: true` option");
    		},
    		m: function mount(target, anchor) {
    			insert_dev(target, div1, anchor);
    			append_dev(div1, div0);
    			append_dev(div0, span);
    			append_dev(span, t0);
    			append_dev(div1, t1);
    			if (if_block) if_block.m(div1, null);

    			if (!mounted) {
    				dispose = [
    					listen_dev(div1, "click", /*clickItem*/ ctx[3], false, false, false),
    					listen_dev(div1, "mouseover", /*hoverItem*/ ctx[4], false, false, false),
    					listen_dev(div1, "focus", /*hoverItem*/ ctx[4], false, false, false)
    				];

    				mounted = true;
    			}
    		},
    		p: function update(ctx, [dirty]) {
    			if (dirty & /*name*/ 1) set_data_dev(t0, /*name*/ ctx[0]);

    			if (/*description*/ ctx[1]) {
    				if (if_block) {
    					if_block.p(ctx, dirty);
    				} else {
    					if_block = create_if_block$4(ctx);
    					if_block.c();
    					if_block.m(div1, null);
    				}
    			} else if (if_block) {
    				if_block.d(1);
    				if_block = null;
    			}

    			if (dirty & /*selected*/ 4) {
    				toggle_class(div1, "selected", /*selected*/ ctx[2]);
    			}
    		},
    		i: noop,
    		o: noop,
    		d: function destroy(detaching) {
    			if (detaching) detach_dev(div1);
    			if (if_block) if_block.d();
    			mounted = false;
    			run_all(dispose);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_fragment$a.name,
    		type: "component",
    		source: "",
    		ctx
    	});

    	return block;
    }

    function instance$a($$self, $$props, $$invalidate) {
    	let { $$slots: slots = {}, $$scope } = $$props;
    	validate_slots('CalculationListItem', slots, []);
    	const dispatch = createEventDispatcher();
    	let { id } = $$props;
    	let { name } = $$props;
    	let { description } = $$props;
    	let { selected } = $$props;
    	const clickItem = () => dispatch("clickItem", { id });
    	const hoverItem = () => dispatch("hoverItem", { id });
    	const writable_props = ['id', 'name', 'description', 'selected'];

    	Object.keys($$props).forEach(key => {
    		if (!~writable_props.indexOf(key) && key.slice(0, 2) !== '$$' && key !== 'slot') console.warn(`<CalculationListItem> was created with unknown prop '${key}'`);
    	});

    	$$self.$$set = $$props => {
    		if ('id' in $$props) $$invalidate(5, id = $$props.id);
    		if ('name' in $$props) $$invalidate(0, name = $$props.name);
    		if ('description' in $$props) $$invalidate(1, description = $$props.description);
    		if ('selected' in $$props) $$invalidate(2, selected = $$props.selected);
    	};

    	$$self.$capture_state = () => ({
    		createEventDispatcher,
    		dispatch,
    		id,
    		name,
    		description,
    		selected,
    		clickItem,
    		hoverItem
    	});

    	$$self.$inject_state = $$props => {
    		if ('id' in $$props) $$invalidate(5, id = $$props.id);
    		if ('name' in $$props) $$invalidate(0, name = $$props.name);
    		if ('description' in $$props) $$invalidate(1, description = $$props.description);
    		if ('selected' in $$props) $$invalidate(2, selected = $$props.selected);
    	};

    	if ($$props && "$$inject" in $$props) {
    		$$self.$inject_state($$props.$$inject);
    	}

    	return [name, description, selected, clickItem, hoverItem, id];
    }

    class CalculationListItem extends SvelteComponentDev {
    	constructor(options) {
    		super(options);

    		init(this, options, instance$a, create_fragment$a, safe_not_equal, {
    			id: 5,
    			name: 0,
    			description: 1,
    			selected: 2
    		});

    		dispatch_dev("SvelteRegisterComponent", {
    			component: this,
    			tagName: "CalculationListItem",
    			options,
    			id: create_fragment$a.name
    		});

    		const { ctx } = this.$$;
    		const props = options.props || {};

    		if (/*id*/ ctx[5] === undefined && !('id' in props)) {
    			console.warn("<CalculationListItem> was created without expected prop 'id'");
    		}

    		if (/*name*/ ctx[0] === undefined && !('name' in props)) {
    			console.warn("<CalculationListItem> was created without expected prop 'name'");
    		}

    		if (/*description*/ ctx[1] === undefined && !('description' in props)) {
    			console.warn("<CalculationListItem> was created without expected prop 'description'");
    		}

    		if (/*selected*/ ctx[2] === undefined && !('selected' in props)) {
    			console.warn("<CalculationListItem> was created without expected prop 'selected'");
    		}
    	}

    	get id() {
    		throw new Error("<CalculationListItem>: Props cannot be read directly from the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}

    	set id(value) {
    		throw new Error("<CalculationListItem>: Props cannot be set directly on the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}

    	get name() {
    		throw new Error("<CalculationListItem>: Props cannot be read directly from the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}

    	set name(value) {
    		throw new Error("<CalculationListItem>: Props cannot be set directly on the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}

    	get description() {
    		throw new Error("<CalculationListItem>: Props cannot be read directly from the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}

    	set description(value) {
    		throw new Error("<CalculationListItem>: Props cannot be set directly on the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}

    	get selected() {
    		throw new Error("<CalculationListItem>: Props cannot be read directly from the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}

    	set selected(value) {
    		throw new Error("<CalculationListItem>: Props cannot be set directly on the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}
    }

    /* src/components/builder/CalculationList.svelte generated by Svelte v3.43.1 */

    const { Object: Object_1$2 } = globals;
    const file$7 = "src/components/builder/CalculationList.svelte";

    function get_each_context$3(ctx, list, i) {
    	const child_ctx = ctx.slice();
    	child_ctx[8] = list[i].id;
    	child_ctx[9] = list[i].name;
    	child_ctx[10] = list[i].description;
    	child_ctx[11] = list[i].selected;
    	return child_ctx;
    }

    // (27:4) {#each _calculations as { id, name, description, selected }
    function create_each_block$3(key_1, ctx) {
    	let first;
    	let calculationlistitem;
    	let current;

    	calculationlistitem = new CalculationListItem({
    			props: {
    				id: /*id*/ ctx[8],
    				name: /*name*/ ctx[9],
    				description: /*description*/ ctx[10],
    				selected: /*selected*/ ctx[11]
    			},
    			$$inline: true
    		});

    	calculationlistitem.$on("hoverItem", /*hoverItem*/ ctx[1]);
    	calculationlistitem.$on("clickItem", /*clickItem*/ ctx[2]);

    	const block = {
    		key: key_1,
    		first: null,
    		c: function create() {
    			first = empty();
    			create_component(calculationlistitem.$$.fragment);
    			this.first = first;
    		},
    		m: function mount(target, anchor) {
    			insert_dev(target, first, anchor);
    			mount_component(calculationlistitem, target, anchor);
    			current = true;
    		},
    		p: function update(new_ctx, dirty) {
    			ctx = new_ctx;
    			const calculationlistitem_changes = {};
    			if (dirty & /*_calculations*/ 1) calculationlistitem_changes.id = /*id*/ ctx[8];
    			if (dirty & /*_calculations*/ 1) calculationlistitem_changes.name = /*name*/ ctx[9];
    			if (dirty & /*_calculations*/ 1) calculationlistitem_changes.description = /*description*/ ctx[10];
    			if (dirty & /*_calculations*/ 1) calculationlistitem_changes.selected = /*selected*/ ctx[11];
    			calculationlistitem.$set(calculationlistitem_changes);
    		},
    		i: function intro(local) {
    			if (current) return;
    			transition_in(calculationlistitem.$$.fragment, local);
    			current = true;
    		},
    		o: function outro(local) {
    			transition_out(calculationlistitem.$$.fragment, local);
    			current = false;
    		},
    		d: function destroy(detaching) {
    			if (detaching) detach_dev(first);
    			destroy_component(calculationlistitem, detaching);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_each_block$3.name,
    		type: "each",
    		source: "(27:4) {#each _calculations as { id, name, description, selected }",
    		ctx
    	});

    	return block;
    }

    function create_fragment$9(ctx) {
    	let div;
    	let each_blocks = [];
    	let each_1_lookup = new Map();
    	let current;
    	let each_value = /*_calculations*/ ctx[0];
    	validate_each_argument(each_value);
    	const get_key = ctx => /*id*/ ctx[8];
    	validate_each_keys(ctx, each_value, get_each_context$3, get_key);

    	for (let i = 0; i < each_value.length; i += 1) {
    		let child_ctx = get_each_context$3(ctx, each_value, i);
    		let key = get_key(child_ctx);
    		each_1_lookup.set(key, each_blocks[i] = create_each_block$3(key, child_ctx));
    	}

    	const block = {
    		c: function create() {
    			div = element("div");

    			for (let i = 0; i < each_blocks.length; i += 1) {
    				each_blocks[i].c();
    			}

    			attr_dev(div, "class", "calculation-list svelte-1gzkwp7");
    			add_location(div, file$7, 25, 0, 758);
    		},
    		l: function claim(nodes) {
    			throw new Error("options.hydrate only works if the component was compiled with the `hydratable: true` option");
    		},
    		m: function mount(target, anchor) {
    			insert_dev(target, div, anchor);

    			for (let i = 0; i < each_blocks.length; i += 1) {
    				each_blocks[i].m(div, null);
    			}

    			current = true;
    		},
    		p: function update(ctx, [dirty]) {
    			if (dirty & /*_calculations, hoverItem, clickItem*/ 7) {
    				each_value = /*_calculations*/ ctx[0];
    				validate_each_argument(each_value);
    				group_outros();
    				validate_each_keys(ctx, each_value, get_each_context$3, get_key);
    				each_blocks = update_keyed_each(each_blocks, dirty, get_key, 1, ctx, each_value, each_1_lookup, div, outro_and_destroy_block, create_each_block$3, null, get_each_context$3);
    				check_outros();
    			}
    		},
    		i: function intro(local) {
    			if (current) return;

    			for (let i = 0; i < each_value.length; i += 1) {
    				transition_in(each_blocks[i]);
    			}

    			current = true;
    		},
    		o: function outro(local) {
    			for (let i = 0; i < each_blocks.length; i += 1) {
    				transition_out(each_blocks[i]);
    			}

    			current = false;
    		},
    		d: function destroy(detaching) {
    			if (detaching) detach_dev(div);

    			for (let i = 0; i < each_blocks.length; i += 1) {
    				each_blocks[i].d();
    			}
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_fragment$9.name,
    		type: "component",
    		source: "",
    		ctx
    	});

    	return block;
    }

    function instance$9($$self, $$props, $$invalidate) {
    	let ids;
    	let _calculations;
    	let { $$slots: slots = {}, $$scope } = $$props;
    	validate_slots('CalculationList', slots, []);
    	let { calculations } = $$props;
    	let { selectedIndex } = $$props;
    	const dispatch = createEventDispatcher();

    	const indexFromId = id => {
    		let index = ids.indexOf(id);
    		return index > -1 ? index : null;
    	};

    	const hoverItem = event => {
    		dispatch("hoverItem", { index: indexFromId(event.detail.id) });
    	};

    	const clickItem = event => {
    		dispatch("clickItem", { index: indexFromId(event.detail.id) });
    	};

    	const writable_props = ['calculations', 'selectedIndex'];

    	Object_1$2.keys($$props).forEach(key => {
    		if (!~writable_props.indexOf(key) && key.slice(0, 2) !== '$$' && key !== 'slot') console.warn(`<CalculationList> was created with unknown prop '${key}'`);
    	});

    	$$self.$$set = $$props => {
    		if ('calculations' in $$props) $$invalidate(3, calculations = $$props.calculations);
    		if ('selectedIndex' in $$props) $$invalidate(4, selectedIndex = $$props.selectedIndex);
    	};

    	$$self.$capture_state = () => ({
    		createEventDispatcher,
    		CalculationListItem,
    		calculations,
    		selectedIndex,
    		dispatch,
    		indexFromId,
    		hoverItem,
    		clickItem,
    		ids,
    		_calculations
    	});

    	$$self.$inject_state = $$props => {
    		if ('calculations' in $$props) $$invalidate(3, calculations = $$props.calculations);
    		if ('selectedIndex' in $$props) $$invalidate(4, selectedIndex = $$props.selectedIndex);
    		if ('ids' in $$props) ids = $$props.ids;
    		if ('_calculations' in $$props) $$invalidate(0, _calculations = $$props._calculations);
    	};

    	if ($$props && "$$inject" in $$props) {
    		$$self.$inject_state($$props.$$inject);
    	}

    	$$self.$$.update = () => {
    		if ($$self.$$.dirty & /*calculations*/ 8) {
    			ids = calculations.map(i => i.id);
    		}

    		if ($$self.$$.dirty & /*calculations, selectedIndex*/ 24) {
    			$$invalidate(0, _calculations = calculations.map((i, ix) => Object.assign({ selected: ix == selectedIndex }, i)));
    		}
    	};

    	return [_calculations, hoverItem, clickItem, calculations, selectedIndex];
    }

    class CalculationList extends SvelteComponentDev {
    	constructor(options) {
    		super(options);
    		init(this, options, instance$9, create_fragment$9, safe_not_equal, { calculations: 3, selectedIndex: 4 });

    		dispatch_dev("SvelteRegisterComponent", {
    			component: this,
    			tagName: "CalculationList",
    			options,
    			id: create_fragment$9.name
    		});

    		const { ctx } = this.$$;
    		const props = options.props || {};

    		if (/*calculations*/ ctx[3] === undefined && !('calculations' in props)) {
    			console.warn("<CalculationList> was created without expected prop 'calculations'");
    		}

    		if (/*selectedIndex*/ ctx[4] === undefined && !('selectedIndex' in props)) {
    			console.warn("<CalculationList> was created without expected prop 'selectedIndex'");
    		}
    	}

    	get calculations() {
    		throw new Error("<CalculationList>: Props cannot be read directly from the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}

    	set calculations(value) {
    		throw new Error("<CalculationList>: Props cannot be set directly on the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}

    	get selectedIndex() {
    		throw new Error("<CalculationList>: Props cannot be read directly from the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}

    	set selectedIndex(value) {
    		throw new Error("<CalculationList>: Props cannot be set directly on the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}
    }

    /* src/components/builder/CalculationSearch.svelte generated by Svelte v3.43.1 */
    const file$6 = "src/components/builder/CalculationSearch.svelte";

    // (50:4) {#if availableCalculations.length > 0}
    function create_if_block_1$2(ctx) {
    	let input;
    	let mounted;
    	let dispose;

    	const block = {
    		c: function create() {
    			input = element("input");
    			attr_dev(input, "placeholder", /*placeholder*/ ctx[1]);
    			add_location(input, file$6, 50, 8, 1635);
    		},
    		m: function mount(target, anchor) {
    			insert_dev(target, input, anchor);
    			set_input_value(input, /*value*/ ctx[2]);

    			if (!mounted) {
    				dispose = [
    					listen_dev(input, "input", /*input_input_handler*/ ctx[10]),
    					listen_dev(input, "focus", /*focus*/ ctx[5], false, false, false),
    					listen_dev(input, "blur", /*blur*/ ctx[6], false, false, false),
    					listen_dev(input, "keydown", /*inputKeyDown*/ ctx[8], false, false, false)
    				];

    				mounted = true;
    			}
    		},
    		p: function update(ctx, dirty) {
    			if (dirty & /*placeholder*/ 2) {
    				attr_dev(input, "placeholder", /*placeholder*/ ctx[1]);
    			}

    			if (dirty & /*value*/ 4 && input.value !== /*value*/ ctx[2]) {
    				set_input_value(input, /*value*/ ctx[2]);
    			}
    		},
    		d: function destroy(detaching) {
    			if (detaching) detach_dev(input);
    			mounted = false;
    			run_all(dispose);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_if_block_1$2.name,
    		type: "if",
    		source: "(50:4) {#if availableCalculations.length > 0}",
    		ctx
    	});

    	return block;
    }

    // (59:4) {#if focused}
    function create_if_block$3(ctx) {
    	let calculationlist;
    	let current;

    	calculationlist = new CalculationList({
    			props: {
    				calculations: /*availableCalculations*/ ctx[0],
    				selectedIndex: /*selectedIndex*/ ctx[3]
    			},
    			$$inline: true
    		});

    	calculationlist.$on("hoverItem", /*hoverItem*/ ctx[7]);
    	calculationlist.$on("clickItem", /*clickItem*/ ctx[9]);

    	const block = {
    		c: function create() {
    			create_component(calculationlist.$$.fragment);
    		},
    		m: function mount(target, anchor) {
    			mount_component(calculationlist, target, anchor);
    			current = true;
    		},
    		p: function update(ctx, dirty) {
    			const calculationlist_changes = {};
    			if (dirty & /*availableCalculations*/ 1) calculationlist_changes.calculations = /*availableCalculations*/ ctx[0];
    			if (dirty & /*selectedIndex*/ 8) calculationlist_changes.selectedIndex = /*selectedIndex*/ ctx[3];
    			calculationlist.$set(calculationlist_changes);
    		},
    		i: function intro(local) {
    			if (current) return;
    			transition_in(calculationlist.$$.fragment, local);
    			current = true;
    		},
    		o: function outro(local) {
    			transition_out(calculationlist.$$.fragment, local);
    			current = false;
    		},
    		d: function destroy(detaching) {
    			destroy_component(calculationlist, detaching);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_if_block$3.name,
    		type: "if",
    		source: "(59:4) {#if focused}",
    		ctx
    	});

    	return block;
    }

    function create_fragment$8(ctx) {
    	let div;
    	let t;
    	let current;
    	let if_block0 = /*availableCalculations*/ ctx[0].length > 0 && create_if_block_1$2(ctx);
    	let if_block1 = /*focused*/ ctx[4] && create_if_block$3(ctx);

    	const block = {
    		c: function create() {
    			div = element("div");
    			if (if_block0) if_block0.c();
    			t = space();
    			if (if_block1) if_block1.c();
    			add_location(div, file$6, 48, 0, 1578);
    		},
    		l: function claim(nodes) {
    			throw new Error("options.hydrate only works if the component was compiled with the `hydratable: true` option");
    		},
    		m: function mount(target, anchor) {
    			insert_dev(target, div, anchor);
    			if (if_block0) if_block0.m(div, null);
    			append_dev(div, t);
    			if (if_block1) if_block1.m(div, null);
    			current = true;
    		},
    		p: function update(ctx, [dirty]) {
    			if (/*availableCalculations*/ ctx[0].length > 0) {
    				if (if_block0) {
    					if_block0.p(ctx, dirty);
    				} else {
    					if_block0 = create_if_block_1$2(ctx);
    					if_block0.c();
    					if_block0.m(div, t);
    				}
    			} else if (if_block0) {
    				if_block0.d(1);
    				if_block0 = null;
    			}

    			if (/*focused*/ ctx[4]) {
    				if (if_block1) {
    					if_block1.p(ctx, dirty);

    					if (dirty & /*focused*/ 16) {
    						transition_in(if_block1, 1);
    					}
    				} else {
    					if_block1 = create_if_block$3(ctx);
    					if_block1.c();
    					transition_in(if_block1, 1);
    					if_block1.m(div, null);
    				}
    			} else if (if_block1) {
    				group_outros();

    				transition_out(if_block1, 1, 1, () => {
    					if_block1 = null;
    				});

    				check_outros();
    			}
    		},
    		i: function intro(local) {
    			if (current) return;
    			transition_in(if_block1);
    			current = true;
    		},
    		o: function outro(local) {
    			transition_out(if_block1);
    			current = false;
    		},
    		d: function destroy(detaching) {
    			if (detaching) detach_dev(div);
    			if (if_block0) if_block0.d();
    			if (if_block1) if_block1.d();
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_fragment$8.name,
    		type: "component",
    		source: "",
    		ctx
    	});

    	return block;
    }

    function instance$8($$self, $$props, $$invalidate) {
    	let { $$slots: slots = {}, $$scope } = $$props;
    	validate_slots('CalculationSearch', slots, []);
    	let { availableCalculations } = $$props;
    	let { placeholder } = $$props;
    	let value; // search input value
    	let selectedIndex = 0; // highlighted item
    	let focused = false; // if input is focused (show search)
    	const dispatch = createEventDispatcher();
    	const focus = () => $$invalidate(4, focused = true);

    	// timeout so that the click on an item in search list has time to be processed
    	// before it's hidden due to blur
    	const blur = () => setTimeout(() => $$invalidate(4, focused = false), 10);

    	const hoverItem = event => {
    		$$invalidate(3, selectedIndex = event.detail.index);
    	};

    	const selectItem = n => {
    		// +1 for next -1 for previous. loops around
    		let selection = selectedIndex + n;

    		if (selection >= availableCalculations.length) {
    			$$invalidate(3, selectedIndex = 0);
    		} else if (selection < 0) {
    			$$invalidate(3, selectedIndex = availableCalculations.length - 1);
    		} else {
    			$$invalidate(3, selectedIndex = selection);
    		}
    	};

    	const inputKeyDown = ({ key }) => {
    		if (key == "ArrowDown") {
    			selectItem(+1);
    		} else if (key == "ArrowUp") {
    			selectItem(-1);
    		} else if (key == "Enter") {
    			dispatch("selectItem", {
    				item: availableCalculations[selectedIndex]
    			});
    		}
    	};

    	const clickItem = event => {
    		dispatch("selectItem", {
    			item: availableCalculations[event.detail.index]
    		});
    	};

    	const writable_props = ['availableCalculations', 'placeholder'];

    	Object.keys($$props).forEach(key => {
    		if (!~writable_props.indexOf(key) && key.slice(0, 2) !== '$$' && key !== 'slot') console.warn(`<CalculationSearch> was created with unknown prop '${key}'`);
    	});

    	function input_input_handler() {
    		value = this.value;
    		$$invalidate(2, value);
    	}

    	$$self.$$set = $$props => {
    		if ('availableCalculations' in $$props) $$invalidate(0, availableCalculations = $$props.availableCalculations);
    		if ('placeholder' in $$props) $$invalidate(1, placeholder = $$props.placeholder);
    	};

    	$$self.$capture_state = () => ({
    		createEventDispatcher,
    		CalculationList,
    		availableCalculations,
    		placeholder,
    		value,
    		selectedIndex,
    		focused,
    		dispatch,
    		focus,
    		blur,
    		hoverItem,
    		selectItem,
    		inputKeyDown,
    		clickItem
    	});

    	$$self.$inject_state = $$props => {
    		if ('availableCalculations' in $$props) $$invalidate(0, availableCalculations = $$props.availableCalculations);
    		if ('placeholder' in $$props) $$invalidate(1, placeholder = $$props.placeholder);
    		if ('value' in $$props) $$invalidate(2, value = $$props.value);
    		if ('selectedIndex' in $$props) $$invalidate(3, selectedIndex = $$props.selectedIndex);
    		if ('focused' in $$props) $$invalidate(4, focused = $$props.focused);
    	};

    	if ($$props && "$$inject" in $$props) {
    		$$self.$inject_state($$props.$$inject);
    	}

    	return [
    		availableCalculations,
    		placeholder,
    		value,
    		selectedIndex,
    		focused,
    		focus,
    		blur,
    		hoverItem,
    		inputKeyDown,
    		clickItem,
    		input_input_handler
    	];
    }

    class CalculationSearch extends SvelteComponentDev {
    	constructor(options) {
    		super(options);
    		init(this, options, instance$8, create_fragment$8, safe_not_equal, { availableCalculations: 0, placeholder: 1 });

    		dispatch_dev("SvelteRegisterComponent", {
    			component: this,
    			tagName: "CalculationSearch",
    			options,
    			id: create_fragment$8.name
    		});

    		const { ctx } = this.$$;
    		const props = options.props || {};

    		if (/*availableCalculations*/ ctx[0] === undefined && !('availableCalculations' in props)) {
    			console.warn("<CalculationSearch> was created without expected prop 'availableCalculations'");
    		}

    		if (/*placeholder*/ ctx[1] === undefined && !('placeholder' in props)) {
    			console.warn("<CalculationSearch> was created without expected prop 'placeholder'");
    		}
    	}

    	get availableCalculations() {
    		throw new Error("<CalculationSearch>: Props cannot be read directly from the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}

    	set availableCalculations(value) {
    		throw new Error("<CalculationSearch>: Props cannot be set directly on the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}

    	get placeholder() {
    		throw new Error("<CalculationSearch>: Props cannot be read directly from the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}

    	set placeholder(value) {
    		throw new Error("<CalculationSearch>: Props cannot be set directly on the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}
    }

    /* src/components/builder/CalculationSelector.svelte generated by Svelte v3.43.1 */
    const file$5 = "src/components/builder/CalculationSelector.svelte";

    function get_each_context$2(ctx, list, i) {
    	const child_ctx = ctx.slice();
    	child_ctx[7] = list[i].id;
    	child_ctx[8] = list[i].name;
    	child_ctx[9] = list[i].type;
    	child_ctx[11] = i;
    	return child_ctx;
    }

    // (24:8) {#if i < calculations.length - 1}
    function create_if_block$2(ctx) {
    	let t;

    	const block = {
    		c: function create() {
    			t = text(",");
    		},
    		m: function mount(target, anchor) {
    			insert_dev(target, t, anchor);
    		},
    		d: function destroy(detaching) {
    			if (detaching) detach_dev(t);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_if_block$2.name,
    		type: "if",
    		source: "(24:8) {#if i < calculations.length - 1}",
    		ctx
    	});

    	return block;
    }

    // (22:4) {#each calculations as { id, name, type }
    function create_each_block$2(key_1, ctx) {
    	let first;
    	let calculationdisplay;
    	let t;
    	let if_block_anchor;
    	let current;

    	calculationdisplay = new CalculationDisplay({
    			props: {
    				id: /*id*/ ctx[7],
    				name: /*name*/ ctx[8],
    				type: /*type*/ ctx[9]
    			},
    			$$inline: true
    		});

    	calculationdisplay.$on("closeItemClick", /*removeItem*/ ctx[5]);
    	let if_block = /*i*/ ctx[11] < /*calculations*/ ctx[3].length - 1 && create_if_block$2(ctx);

    	const block = {
    		key: key_1,
    		first: null,
    		c: function create() {
    			first = empty();
    			create_component(calculationdisplay.$$.fragment);
    			t = space();
    			if (if_block) if_block.c();
    			if_block_anchor = empty();
    			this.first = first;
    		},
    		m: function mount(target, anchor) {
    			insert_dev(target, first, anchor);
    			mount_component(calculationdisplay, target, anchor);
    			insert_dev(target, t, anchor);
    			if (if_block) if_block.m(target, anchor);
    			insert_dev(target, if_block_anchor, anchor);
    			current = true;
    		},
    		p: function update(new_ctx, dirty) {
    			ctx = new_ctx;
    			const calculationdisplay_changes = {};
    			if (dirty & /*calculations*/ 8) calculationdisplay_changes.id = /*id*/ ctx[7];
    			if (dirty & /*calculations*/ 8) calculationdisplay_changes.name = /*name*/ ctx[8];
    			if (dirty & /*calculations*/ 8) calculationdisplay_changes.type = /*type*/ ctx[9];
    			calculationdisplay.$set(calculationdisplay_changes);

    			if (/*i*/ ctx[11] < /*calculations*/ ctx[3].length - 1) {
    				if (if_block) ; else {
    					if_block = create_if_block$2(ctx);
    					if_block.c();
    					if_block.m(if_block_anchor.parentNode, if_block_anchor);
    				}
    			} else if (if_block) {
    				if_block.d(1);
    				if_block = null;
    			}
    		},
    		i: function intro(local) {
    			if (current) return;
    			transition_in(calculationdisplay.$$.fragment, local);
    			current = true;
    		},
    		o: function outro(local) {
    			transition_out(calculationdisplay.$$.fragment, local);
    			current = false;
    		},
    		d: function destroy(detaching) {
    			if (detaching) detach_dev(first);
    			destroy_component(calculationdisplay, detaching);
    			if (detaching) detach_dev(t);
    			if (if_block) if_block.d(detaching);
    			if (detaching) detach_dev(if_block_anchor);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_each_block$2.name,
    		type: "each",
    		source: "(22:4) {#each calculations as { id, name, type }",
    		ctx
    	});

    	return block;
    }

    function create_fragment$7(ctx) {
    	let div;
    	let span;
    	let t0;
    	let t1;
    	let each_blocks = [];
    	let each_1_lookup = new Map();
    	let t2;
    	let calculationsearch;
    	let current;
    	let each_value = /*calculations*/ ctx[3];
    	validate_each_argument(each_value);
    	const get_key = ctx => /*id*/ ctx[7];
    	validate_each_keys(ctx, each_value, get_each_context$2, get_key);

    	for (let i = 0; i < each_value.length; i += 1) {
    		let child_ctx = get_each_context$2(ctx, each_value, i);
    		let key = get_key(child_ctx);
    		each_1_lookup.set(key, each_blocks[i] = create_each_block$2(key, child_ctx));
    	}

    	calculationsearch = new CalculationSearch({
    			props: {
    				availableCalculations: /*availableCalculations*/ ctx[2],
    				placeholder: /*placeholder*/ ctx[1]
    			},
    			$$inline: true
    		});

    	calculationsearch.$on("selectItem", /*addItem*/ ctx[4]);

    	const block = {
    		c: function create() {
    			div = element("div");
    			span = element("span");
    			t0 = text(/*title*/ ctx[0]);
    			t1 = space();

    			for (let i = 0; i < each_blocks.length; i += 1) {
    				each_blocks[i].c();
    			}

    			t2 = space();
    			create_component(calculationsearch.$$.fragment);
    			add_location(span, file$5, 20, 4, 563);
    			add_location(div, file$5, 19, 0, 553);
    		},
    		l: function claim(nodes) {
    			throw new Error("options.hydrate only works if the component was compiled with the `hydratable: true` option");
    		},
    		m: function mount(target, anchor) {
    			insert_dev(target, div, anchor);
    			append_dev(div, span);
    			append_dev(span, t0);
    			append_dev(div, t1);

    			for (let i = 0; i < each_blocks.length; i += 1) {
    				each_blocks[i].m(div, null);
    			}

    			append_dev(div, t2);
    			mount_component(calculationsearch, div, null);
    			current = true;
    		},
    		p: function update(ctx, [dirty]) {
    			if (!current || dirty & /*title*/ 1) set_data_dev(t0, /*title*/ ctx[0]);

    			if (dirty & /*calculations, removeItem*/ 40) {
    				each_value = /*calculations*/ ctx[3];
    				validate_each_argument(each_value);
    				group_outros();
    				validate_each_keys(ctx, each_value, get_each_context$2, get_key);
    				each_blocks = update_keyed_each(each_blocks, dirty, get_key, 1, ctx, each_value, each_1_lookup, div, outro_and_destroy_block, create_each_block$2, t2, get_each_context$2);
    				check_outros();
    			}

    			const calculationsearch_changes = {};
    			if (dirty & /*availableCalculations*/ 4) calculationsearch_changes.availableCalculations = /*availableCalculations*/ ctx[2];
    			if (dirty & /*placeholder*/ 2) calculationsearch_changes.placeholder = /*placeholder*/ ctx[1];
    			calculationsearch.$set(calculationsearch_changes);
    		},
    		i: function intro(local) {
    			if (current) return;

    			for (let i = 0; i < each_value.length; i += 1) {
    				transition_in(each_blocks[i]);
    			}

    			transition_in(calculationsearch.$$.fragment, local);
    			current = true;
    		},
    		o: function outro(local) {
    			for (let i = 0; i < each_blocks.length; i += 1) {
    				transition_out(each_blocks[i]);
    			}

    			transition_out(calculationsearch.$$.fragment, local);
    			current = false;
    		},
    		d: function destroy(detaching) {
    			if (detaching) detach_dev(div);

    			for (let i = 0; i < each_blocks.length; i += 1) {
    				each_blocks[i].d();
    			}

    			destroy_component(calculationsearch);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_fragment$7.name,
    		type: "component",
    		source: "",
    		ctx
    	});

    	return block;
    }

    function instance$7($$self, $$props, $$invalidate) {
    	let { $$slots: slots = {}, $$scope } = $$props;
    	validate_slots('CalculationSelector', slots, []);
    	let { title } = $$props;
    	let { placeholder } = $$props;
    	let { availableCalculations } = $$props;
    	let { calculations } = $$props;
    	const dispatch = createEventDispatcher();

    	const addItem = event => {
    		dispatch("addCalculation", event.detail);
    	};

    	const removeItem = event => {
    		dispatch("removeCalculation", event.detail);
    	};

    	const writable_props = ['title', 'placeholder', 'availableCalculations', 'calculations'];

    	Object.keys($$props).forEach(key => {
    		if (!~writable_props.indexOf(key) && key.slice(0, 2) !== '$$' && key !== 'slot') console.warn(`<CalculationSelector> was created with unknown prop '${key}'`);
    	});

    	$$self.$$set = $$props => {
    		if ('title' in $$props) $$invalidate(0, title = $$props.title);
    		if ('placeholder' in $$props) $$invalidate(1, placeholder = $$props.placeholder);
    		if ('availableCalculations' in $$props) $$invalidate(2, availableCalculations = $$props.availableCalculations);
    		if ('calculations' in $$props) $$invalidate(3, calculations = $$props.calculations);
    	};

    	$$self.$capture_state = () => ({
    		createEventDispatcher,
    		CalculationDisplay,
    		CalculationSearch,
    		title,
    		placeholder,
    		availableCalculations,
    		calculations,
    		dispatch,
    		addItem,
    		removeItem
    	});

    	$$self.$inject_state = $$props => {
    		if ('title' in $$props) $$invalidate(0, title = $$props.title);
    		if ('placeholder' in $$props) $$invalidate(1, placeholder = $$props.placeholder);
    		if ('availableCalculations' in $$props) $$invalidate(2, availableCalculations = $$props.availableCalculations);
    		if ('calculations' in $$props) $$invalidate(3, calculations = $$props.calculations);
    	};

    	if ($$props && "$$inject" in $$props) {
    		$$self.$inject_state($$props.$$inject);
    	}

    	return [title, placeholder, availableCalculations, calculations, addItem, removeItem];
    }

    class CalculationSelector extends SvelteComponentDev {
    	constructor(options) {
    		super(options);

    		init(this, options, instance$7, create_fragment$7, safe_not_equal, {
    			title: 0,
    			placeholder: 1,
    			availableCalculations: 2,
    			calculations: 3
    		});

    		dispatch_dev("SvelteRegisterComponent", {
    			component: this,
    			tagName: "CalculationSelector",
    			options,
    			id: create_fragment$7.name
    		});

    		const { ctx } = this.$$;
    		const props = options.props || {};

    		if (/*title*/ ctx[0] === undefined && !('title' in props)) {
    			console.warn("<CalculationSelector> was created without expected prop 'title'");
    		}

    		if (/*placeholder*/ ctx[1] === undefined && !('placeholder' in props)) {
    			console.warn("<CalculationSelector> was created without expected prop 'placeholder'");
    		}

    		if (/*availableCalculations*/ ctx[2] === undefined && !('availableCalculations' in props)) {
    			console.warn("<CalculationSelector> was created without expected prop 'availableCalculations'");
    		}

    		if (/*calculations*/ ctx[3] === undefined && !('calculations' in props)) {
    			console.warn("<CalculationSelector> was created without expected prop 'calculations'");
    		}
    	}

    	get title() {
    		throw new Error("<CalculationSelector>: Props cannot be read directly from the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}

    	set title(value) {
    		throw new Error("<CalculationSelector>: Props cannot be set directly on the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}

    	get placeholder() {
    		throw new Error("<CalculationSelector>: Props cannot be read directly from the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}

    	set placeholder(value) {
    		throw new Error("<CalculationSelector>: Props cannot be set directly on the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}

    	get availableCalculations() {
    		throw new Error("<CalculationSelector>: Props cannot be read directly from the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}

    	set availableCalculations(value) {
    		throw new Error("<CalculationSelector>: Props cannot be set directly on the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}

    	get calculations() {
    		throw new Error("<CalculationSelector>: Props cannot be read directly from the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}

    	set calculations(value) {
    		throw new Error("<CalculationSelector>: Props cannot be set directly on the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}
    }

    /* src/components/display/BigNumber.svelte generated by Svelte v3.43.1 */

    const file$4 = "src/components/display/BigNumber.svelte";

    function create_fragment$6(ctx) {
    	let div;
    	let h1;
    	let t0;
    	let t1;
    	let span;
    	let t2;

    	const block = {
    		c: function create() {
    			div = element("div");
    			h1 = element("h1");
    			t0 = text(/*name*/ ctx[0]);
    			t1 = space();
    			span = element("span");
    			t2 = text(/*formattedValue*/ ctx[1]);
    			attr_dev(h1, "class", "svelte-mi0gkn");
    			add_location(h1, file$4, 9, 4, 196);
    			attr_dev(span, "class", "svelte-mi0gkn");
    			add_location(span, file$4, 10, 4, 216);
    			attr_dev(div, "class", "svelte-mi0gkn");
    			add_location(div, file$4, 8, 0, 186);
    		},
    		l: function claim(nodes) {
    			throw new Error("options.hydrate only works if the component was compiled with the `hydratable: true` option");
    		},
    		m: function mount(target, anchor) {
    			insert_dev(target, div, anchor);
    			append_dev(div, h1);
    			append_dev(h1, t0);
    			append_dev(div, t1);
    			append_dev(div, span);
    			append_dev(span, t2);
    		},
    		p: function update(ctx, [dirty]) {
    			if (dirty & /*name*/ 1) set_data_dev(t0, /*name*/ ctx[0]);
    			if (dirty & /*formattedValue*/ 2) set_data_dev(t2, /*formattedValue*/ ctx[1]);
    		},
    		i: noop,
    		o: noop,
    		d: function destroy(detaching) {
    			if (detaching) detach_dev(div);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_fragment$6.name,
    		type: "component",
    		source: "",
    		ctx
    	});

    	return block;
    }

    function instance$6($$self, $$props, $$invalidate) {
    	let formattedValue;
    	let { $$slots: slots = {}, $$scope } = $$props;
    	validate_slots('BigNumber', slots, []);
    	let { name } = $$props;
    	let { value } = $$props;
    	let { format = null } = $$props;
    	const writable_props = ['name', 'value', 'format'];

    	Object.keys($$props).forEach(key => {
    		if (!~writable_props.indexOf(key) && key.slice(0, 2) !== '$$' && key !== 'slot') console.warn(`<BigNumber> was created with unknown prop '${key}'`);
    	});

    	$$self.$$set = $$props => {
    		if ('name' in $$props) $$invalidate(0, name = $$props.name);
    		if ('value' in $$props) $$invalidate(2, value = $$props.value);
    		if ('format' in $$props) $$invalidate(3, format = $$props.format);
    	};

    	$$self.$capture_state = () => ({ name, value, format, formattedValue });

    	$$self.$inject_state = $$props => {
    		if ('name' in $$props) $$invalidate(0, name = $$props.name);
    		if ('value' in $$props) $$invalidate(2, value = $$props.value);
    		if ('format' in $$props) $$invalidate(3, format = $$props.format);
    		if ('formattedValue' in $$props) $$invalidate(1, formattedValue = $$props.formattedValue);
    	};

    	if ($$props && "$$inject" in $$props) {
    		$$self.$inject_state($$props.$$inject);
    	}

    	$$self.$$.update = () => {
    		if ($$self.$$.dirty & /*format, value*/ 12) {
    			$$invalidate(1, formattedValue = format === null ? value : value); // TODO: formatting with d3-format
    		}
    	};

    	return [name, formattedValue, value, format];
    }

    class BigNumber extends SvelteComponentDev {
    	constructor(options) {
    		super(options);
    		init(this, options, instance$6, create_fragment$6, safe_not_equal, { name: 0, value: 2, format: 3 });

    		dispatch_dev("SvelteRegisterComponent", {
    			component: this,
    			tagName: "BigNumber",
    			options,
    			id: create_fragment$6.name
    		});

    		const { ctx } = this.$$;
    		const props = options.props || {};

    		if (/*name*/ ctx[0] === undefined && !('name' in props)) {
    			console.warn("<BigNumber> was created without expected prop 'name'");
    		}

    		if (/*value*/ ctx[2] === undefined && !('value' in props)) {
    			console.warn("<BigNumber> was created without expected prop 'value'");
    		}
    	}

    	get name() {
    		throw new Error("<BigNumber>: Props cannot be read directly from the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}

    	set name(value) {
    		throw new Error("<BigNumber>: Props cannot be set directly on the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}

    	get value() {
    		throw new Error("<BigNumber>: Props cannot be read directly from the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}

    	set value(value) {
    		throw new Error("<BigNumber>: Props cannot be set directly on the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}

    	get format() {
    		throw new Error("<BigNumber>: Props cannot be read directly from the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}

    	set format(value) {
    		throw new Error("<BigNumber>: Props cannot be set directly on the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}
    }

    /* src/components/display/BigNumbers.svelte generated by Svelte v3.43.1 */

    const { Object: Object_1$1 } = globals;
    const file$3 = "src/components/display/BigNumbers.svelte";

    function get_each_context$1(ctx, list, i) {
    	const child_ctx = ctx.slice();
    	child_ctx[2] = list[i].name;
    	child_ctx[3] = list[i].value;
    	return child_ctx;
    }

    // (18:4) {#each values as { name, value }}
    function create_each_block$1(ctx) {
    	let bignumber;
    	let current;

    	bignumber = new BigNumber({
    			props: {
    				name: /*name*/ ctx[2],
    				value: /*value*/ ctx[3]
    			},
    			$$inline: true
    		});

    	const block = {
    		c: function create() {
    			create_component(bignumber.$$.fragment);
    		},
    		m: function mount(target, anchor) {
    			mount_component(bignumber, target, anchor);
    			current = true;
    		},
    		p: function update(ctx, dirty) {
    			const bignumber_changes = {};
    			if (dirty & /*values*/ 1) bignumber_changes.name = /*name*/ ctx[2];
    			if (dirty & /*values*/ 1) bignumber_changes.value = /*value*/ ctx[3];
    			bignumber.$set(bignumber_changes);
    		},
    		i: function intro(local) {
    			if (current) return;
    			transition_in(bignumber.$$.fragment, local);
    			current = true;
    		},
    		o: function outro(local) {
    			transition_out(bignumber.$$.fragment, local);
    			current = false;
    		},
    		d: function destroy(detaching) {
    			destroy_component(bignumber, detaching);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_each_block$1.name,
    		type: "each",
    		source: "(18:4) {#each values as { name, value }}",
    		ctx
    	});

    	return block;
    }

    function create_fragment$5(ctx) {
    	let div;
    	let current;
    	let each_value = /*values*/ ctx[0];
    	validate_each_argument(each_value);
    	let each_blocks = [];

    	for (let i = 0; i < each_value.length; i += 1) {
    		each_blocks[i] = create_each_block$1(get_each_context$1(ctx, each_value, i));
    	}

    	const out = i => transition_out(each_blocks[i], 1, 1, () => {
    		each_blocks[i] = null;
    	});

    	const block = {
    		c: function create() {
    			div = element("div");

    			for (let i = 0; i < each_blocks.length; i += 1) {
    				each_blocks[i].c();
    			}

    			attr_dev(div, "class", "big-numbers svelte-s599iq");
    			add_location(div, file$3, 16, 0, 375);
    		},
    		l: function claim(nodes) {
    			throw new Error("options.hydrate only works if the component was compiled with the `hydratable: true` option");
    		},
    		m: function mount(target, anchor) {
    			insert_dev(target, div, anchor);

    			for (let i = 0; i < each_blocks.length; i += 1) {
    				each_blocks[i].m(div, null);
    			}

    			current = true;
    		},
    		p: function update(ctx, [dirty]) {
    			if (dirty & /*values*/ 1) {
    				each_value = /*values*/ ctx[0];
    				validate_each_argument(each_value);
    				let i;

    				for (i = 0; i < each_value.length; i += 1) {
    					const child_ctx = get_each_context$1(ctx, each_value, i);

    					if (each_blocks[i]) {
    						each_blocks[i].p(child_ctx, dirty);
    						transition_in(each_blocks[i], 1);
    					} else {
    						each_blocks[i] = create_each_block$1(child_ctx);
    						each_blocks[i].c();
    						transition_in(each_blocks[i], 1);
    						each_blocks[i].m(div, null);
    					}
    				}

    				group_outros();

    				for (i = each_value.length; i < each_blocks.length; i += 1) {
    					out(i);
    				}

    				check_outros();
    			}
    		},
    		i: function intro(local) {
    			if (current) return;

    			for (let i = 0; i < each_value.length; i += 1) {
    				transition_in(each_blocks[i]);
    			}

    			current = true;
    		},
    		o: function outro(local) {
    			each_blocks = each_blocks.filter(Boolean);

    			for (let i = 0; i < each_blocks.length; i += 1) {
    				transition_out(each_blocks[i]);
    			}

    			current = false;
    		},
    		d: function destroy(detaching) {
    			if (detaching) detach_dev(div);
    			destroy_each(each_blocks, detaching);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_fragment$5.name,
    		type: "component",
    		source: "",
    		ctx
    	});

    	return block;
    }

    function instance$5($$self, $$props, $$invalidate) {
    	let { $$slots: slots = {}, $$scope } = $$props;
    	validate_slots('BigNumbers', slots, []);
    	let { queryResult } = $$props;
    	let values = [];
    	const writable_props = ['queryResult'];

    	Object_1$1.keys($$props).forEach(key => {
    		if (!~writable_props.indexOf(key) && key.slice(0, 2) !== '$$' && key !== 'slot') console.warn(`<BigNumbers> was created with unknown prop '${key}'`);
    	});

    	$$self.$$set = $$props => {
    		if ('queryResult' in $$props) $$invalidate(1, queryResult = $$props.queryResult);
    	};

    	$$self.$capture_state = () => ({ BigNumber, queryResult, values });

    	$$self.$inject_state = $$props => {
    		if ('queryResult' in $$props) $$invalidate(1, queryResult = $$props.queryResult);
    		if ('values' in $$props) $$invalidate(0, values = $$props.values);
    	};

    	if ($$props && "$$inject" in $$props) {
    		$$self.$inject_state($$props.$$inject);
    	}

    	$$self.$$.update = () => {
    		if ($$self.$$.dirty & /*queryResult*/ 2) {
    			if (queryResult.data.length === 1) {
    				let data = queryResult.data[0];
    				let meta = queryResult.metadata.columns;
    				$$invalidate(0, values = Object.keys(data).map(k => ({ name: meta[k], value: data[k] })));
    			}
    		}
    	};

    	return [values, queryResult];
    }

    class BigNumbers extends SvelteComponentDev {
    	constructor(options) {
    		super(options);
    		init(this, options, instance$5, create_fragment$5, safe_not_equal, { queryResult: 1 });

    		dispatch_dev("SvelteRegisterComponent", {
    			component: this,
    			tagName: "BigNumbers",
    			options,
    			id: create_fragment$5.name
    		});

    		const { ctx } = this.$$;
    		const props = options.props || {};

    		if (/*queryResult*/ ctx[1] === undefined && !('queryResult' in props)) {
    			console.warn("<BigNumbers> was created without expected prop 'queryResult'");
    		}
    	}

    	get queryResult() {
    		throw new Error("<BigNumbers>: Props cannot be read directly from the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}

    	set queryResult(value) {
    		throw new Error("<BigNumbers>: Props cannot be set directly on the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}
    }

    /* src/components/display/TableDisplay.svelte generated by Svelte v3.43.1 */

    const { Object: Object_1 } = globals;
    const file$2 = "src/components/display/TableDisplay.svelte";

    function get_each_context(ctx, list, i) {
    	const child_ctx = ctx.slice();
    	child_ctx[3] = list[i];
    	return child_ctx;
    }

    function get_each_context_1(ctx, list, i) {
    	const child_ctx = ctx.slice();
    	child_ctx[6] = list[i];
    	return child_ctx;
    }

    function get_each_context_2(ctx, list, i) {
    	const child_ctx = ctx.slice();
    	child_ctx[9] = list[i];
    	return child_ctx;
    }

    // (11:16) {#each names as name (name)}
    function create_each_block_2(key_1, ctx) {
    	let th;
    	let t_value = /*name*/ ctx[9] + "";
    	let t;

    	const block = {
    		key: key_1,
    		first: null,
    		c: function create() {
    			th = element("th");
    			t = text(t_value);
    			attr_dev(th, "class", "svelte-10mmylh");
    			add_location(th, file$2, 11, 20, 308);
    			this.first = th;
    		},
    		m: function mount(target, anchor) {
    			insert_dev(target, th, anchor);
    			append_dev(th, t);
    		},
    		p: function update(new_ctx, dirty) {
    			ctx = new_ctx;
    			if (dirty & /*names*/ 4 && t_value !== (t_value = /*name*/ ctx[9] + "")) set_data_dev(t, t_value);
    		},
    		d: function destroy(detaching) {
    			if (detaching) detach_dev(th);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_each_block_2.name,
    		type: "each",
    		source: "(11:16) {#each names as name (name)}",
    		ctx
    	});

    	return block;
    }

    // (19:20) {#each keys as k (k)}
    function create_each_block_1(key_1, ctx) {
    	let td;
    	let t_value = /*row*/ ctx[3][/*k*/ ctx[6]] + "";
    	let t;

    	const block = {
    		key: key_1,
    		first: null,
    		c: function create() {
    			td = element("td");
    			t = text(t_value);
    			attr_dev(td, "class", "svelte-10mmylh");
    			add_location(td, file$2, 19, 24, 530);
    			this.first = td;
    		},
    		m: function mount(target, anchor) {
    			insert_dev(target, td, anchor);
    			append_dev(td, t);
    		},
    		p: function update(new_ctx, dirty) {
    			ctx = new_ctx;
    			if (dirty & /*queryResult, keys*/ 3 && t_value !== (t_value = /*row*/ ctx[3][/*k*/ ctx[6]] + "")) set_data_dev(t, t_value);
    		},
    		d: function destroy(detaching) {
    			if (detaching) detach_dev(td);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_each_block_1.name,
    		type: "each",
    		source: "(19:20) {#each keys as k (k)}",
    		ctx
    	});

    	return block;
    }

    // (17:12) {#each queryResult.data as row}
    function create_each_block(ctx) {
    	let tr;
    	let each_blocks = [];
    	let each_1_lookup = new Map();
    	let t;
    	let each_value_1 = /*keys*/ ctx[1];
    	validate_each_argument(each_value_1);
    	const get_key = ctx => /*k*/ ctx[6];
    	validate_each_keys(ctx, each_value_1, get_each_context_1, get_key);

    	for (let i = 0; i < each_value_1.length; i += 1) {
    		let child_ctx = get_each_context_1(ctx, each_value_1, i);
    		let key = get_key(child_ctx);
    		each_1_lookup.set(key, each_blocks[i] = create_each_block_1(key, child_ctx));
    	}

    	const block = {
    		c: function create() {
    			tr = element("tr");

    			for (let i = 0; i < each_blocks.length; i += 1) {
    				each_blocks[i].c();
    			}

    			t = space();
    			add_location(tr, file$2, 17, 16, 459);
    		},
    		m: function mount(target, anchor) {
    			insert_dev(target, tr, anchor);

    			for (let i = 0; i < each_blocks.length; i += 1) {
    				each_blocks[i].m(tr, null);
    			}

    			append_dev(tr, t);
    		},
    		p: function update(ctx, dirty) {
    			if (dirty & /*queryResult, keys*/ 3) {
    				each_value_1 = /*keys*/ ctx[1];
    				validate_each_argument(each_value_1);
    				validate_each_keys(ctx, each_value_1, get_each_context_1, get_key);
    				each_blocks = update_keyed_each(each_blocks, dirty, get_key, 1, ctx, each_value_1, each_1_lookup, tr, destroy_block, create_each_block_1, t, get_each_context_1);
    			}
    		},
    		d: function destroy(detaching) {
    			if (detaching) detach_dev(tr);

    			for (let i = 0; i < each_blocks.length; i += 1) {
    				each_blocks[i].d();
    			}
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_each_block.name,
    		type: "each",
    		source: "(17:12) {#each queryResult.data as row}",
    		ctx
    	});

    	return block;
    }

    function create_fragment$4(ctx) {
    	let div;
    	let table;
    	let thead;
    	let tr;
    	let each_blocks_1 = [];
    	let each0_lookup = new Map();
    	let t;
    	let tbody;
    	let each_value_2 = /*names*/ ctx[2];
    	validate_each_argument(each_value_2);
    	const get_key = ctx => /*name*/ ctx[9];
    	validate_each_keys(ctx, each_value_2, get_each_context_2, get_key);

    	for (let i = 0; i < each_value_2.length; i += 1) {
    		let child_ctx = get_each_context_2(ctx, each_value_2, i);
    		let key = get_key(child_ctx);
    		each0_lookup.set(key, each_blocks_1[i] = create_each_block_2(key, child_ctx));
    	}

    	let each_value = /*queryResult*/ ctx[0].data;
    	validate_each_argument(each_value);
    	let each_blocks = [];

    	for (let i = 0; i < each_value.length; i += 1) {
    		each_blocks[i] = create_each_block(get_each_context(ctx, each_value, i));
    	}

    	const block = {
    		c: function create() {
    			div = element("div");
    			table = element("table");
    			thead = element("thead");
    			tr = element("tr");

    			for (let i = 0; i < each_blocks_1.length; i += 1) {
    				each_blocks_1[i].c();
    			}

    			t = space();
    			tbody = element("tbody");

    			for (let i = 0; i < each_blocks.length; i += 1) {
    				each_blocks[i].c();
    			}

    			add_location(tr, file$2, 9, 12, 238);
    			add_location(thead, file$2, 8, 8, 218);
    			add_location(tbody, file$2, 15, 8, 391);
    			attr_dev(table, "class", "svelte-10mmylh");
    			add_location(table, file$2, 7, 4, 202);
    			attr_dev(div, "class", "table-wrapper svelte-10mmylh");
    			add_location(div, file$2, 6, 0, 170);
    		},
    		l: function claim(nodes) {
    			throw new Error("options.hydrate only works if the component was compiled with the `hydratable: true` option");
    		},
    		m: function mount(target, anchor) {
    			insert_dev(target, div, anchor);
    			append_dev(div, table);
    			append_dev(table, thead);
    			append_dev(thead, tr);

    			for (let i = 0; i < each_blocks_1.length; i += 1) {
    				each_blocks_1[i].m(tr, null);
    			}

    			append_dev(table, t);
    			append_dev(table, tbody);

    			for (let i = 0; i < each_blocks.length; i += 1) {
    				each_blocks[i].m(tbody, null);
    			}
    		},
    		p: function update(ctx, [dirty]) {
    			if (dirty & /*names*/ 4) {
    				each_value_2 = /*names*/ ctx[2];
    				validate_each_argument(each_value_2);
    				validate_each_keys(ctx, each_value_2, get_each_context_2, get_key);
    				each_blocks_1 = update_keyed_each(each_blocks_1, dirty, get_key, 1, ctx, each_value_2, each0_lookup, tr, destroy_block, create_each_block_2, null, get_each_context_2);
    			}

    			if (dirty & /*keys, queryResult*/ 3) {
    				each_value = /*queryResult*/ ctx[0].data;
    				validate_each_argument(each_value);
    				let i;

    				for (i = 0; i < each_value.length; i += 1) {
    					const child_ctx = get_each_context(ctx, each_value, i);

    					if (each_blocks[i]) {
    						each_blocks[i].p(child_ctx, dirty);
    					} else {
    						each_blocks[i] = create_each_block(child_ctx);
    						each_blocks[i].c();
    						each_blocks[i].m(tbody, null);
    					}
    				}

    				for (; i < each_blocks.length; i += 1) {
    					each_blocks[i].d(1);
    				}

    				each_blocks.length = each_value.length;
    			}
    		},
    		i: noop,
    		o: noop,
    		d: function destroy(detaching) {
    			if (detaching) detach_dev(div);

    			for (let i = 0; i < each_blocks_1.length; i += 1) {
    				each_blocks_1[i].d();
    			}

    			destroy_each(each_blocks, detaching);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_fragment$4.name,
    		type: "component",
    		source: "",
    		ctx
    	});

    	return block;
    }

    function instance$4($$self, $$props, $$invalidate) {
    	let keys;
    	let names;
    	let { $$slots: slots = {}, $$scope } = $$props;
    	validate_slots('TableDisplay', slots, []);
    	let { queryResult } = $$props;
    	const writable_props = ['queryResult'];

    	Object_1.keys($$props).forEach(key => {
    		if (!~writable_props.indexOf(key) && key.slice(0, 2) !== '$$' && key !== 'slot') console.warn(`<TableDisplay> was created with unknown prop '${key}'`);
    	});

    	$$self.$$set = $$props => {
    		if ('queryResult' in $$props) $$invalidate(0, queryResult = $$props.queryResult);
    	};

    	$$self.$capture_state = () => ({ queryResult, keys, names });

    	$$self.$inject_state = $$props => {
    		if ('queryResult' in $$props) $$invalidate(0, queryResult = $$props.queryResult);
    		if ('keys' in $$props) $$invalidate(1, keys = $$props.keys);
    		if ('names' in $$props) $$invalidate(2, names = $$props.names);
    	};

    	if ($$props && "$$inject" in $$props) {
    		$$self.$inject_state($$props.$$inject);
    	}

    	$$self.$$.update = () => {
    		if ($$self.$$.dirty & /*queryResult*/ 1) {
    			$$invalidate(1, keys = Object.keys(queryResult.metadata.columns));
    		}

    		if ($$self.$$.dirty & /*keys, queryResult*/ 3) {
    			$$invalidate(2, names = keys.map(k => queryResult.metadata.columns[k]));
    		}
    	};

    	return [queryResult, keys, names];
    }

    class TableDisplay extends SvelteComponentDev {
    	constructor(options) {
    		super(options);
    		init(this, options, instance$4, create_fragment$4, safe_not_equal, { queryResult: 0 });

    		dispatch_dev("SvelteRegisterComponent", {
    			component: this,
    			tagName: "TableDisplay",
    			options,
    			id: create_fragment$4.name
    		});

    		const { ctx } = this.$$;
    		const props = options.props || {};

    		if (/*queryResult*/ ctx[0] === undefined && !('queryResult' in props)) {
    			console.warn("<TableDisplay> was created without expected prop 'queryResult'");
    		}
    	}

    	get queryResult() {
    		throw new Error("<TableDisplay>: Props cannot be read directly from the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}

    	set queryResult(value) {
    		throw new Error("<TableDisplay>: Props cannot be set directly on the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}
    }

    /* src/components/display/QueryResultDisplay.svelte generated by Svelte v3.43.1 */

    // (10:38) 
    function create_if_block_1$1(ctx) {
    	let tabledisplay;
    	let current;

    	tabledisplay = new TableDisplay({
    			props: { queryResult: /*queryResult*/ ctx[0] },
    			$$inline: true
    		});

    	const block = {
    		c: function create() {
    			create_component(tabledisplay.$$.fragment);
    		},
    		m: function mount(target, anchor) {
    			mount_component(tabledisplay, target, anchor);
    			current = true;
    		},
    		p: function update(ctx, dirty) {
    			const tabledisplay_changes = {};
    			if (dirty & /*queryResult*/ 1) tabledisplay_changes.queryResult = /*queryResult*/ ctx[0];
    			tabledisplay.$set(tabledisplay_changes);
    		},
    		i: function intro(local) {
    			if (current) return;
    			transition_in(tabledisplay.$$.fragment, local);
    			current = true;
    		},
    		o: function outro(local) {
    			transition_out(tabledisplay.$$.fragment, local);
    			current = false;
    		},
    		d: function destroy(detaching) {
    			destroy_component(tabledisplay, detaching);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_if_block_1$1.name,
    		type: "if",
    		source: "(10:38) ",
    		ctx
    	});

    	return block;
    }

    // (8:0) {#if queryResult.data.length === 1}
    function create_if_block$1(ctx) {
    	let bignumbers;
    	let current;

    	bignumbers = new BigNumbers({
    			props: { queryResult: /*queryResult*/ ctx[0] },
    			$$inline: true
    		});

    	const block = {
    		c: function create() {
    			create_component(bignumbers.$$.fragment);
    		},
    		m: function mount(target, anchor) {
    			mount_component(bignumbers, target, anchor);
    			current = true;
    		},
    		p: function update(ctx, dirty) {
    			const bignumbers_changes = {};
    			if (dirty & /*queryResult*/ 1) bignumbers_changes.queryResult = /*queryResult*/ ctx[0];
    			bignumbers.$set(bignumbers_changes);
    		},
    		i: function intro(local) {
    			if (current) return;
    			transition_in(bignumbers.$$.fragment, local);
    			current = true;
    		},
    		o: function outro(local) {
    			transition_out(bignumbers.$$.fragment, local);
    			current = false;
    		},
    		d: function destroy(detaching) {
    			destroy_component(bignumbers, detaching);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_if_block$1.name,
    		type: "if",
    		source: "(8:0) {#if queryResult.data.length === 1}",
    		ctx
    	});

    	return block;
    }

    function create_fragment$3(ctx) {
    	let current_block_type_index;
    	let if_block;
    	let if_block_anchor;
    	let current;
    	const if_block_creators = [create_if_block$1, create_if_block_1$1];
    	const if_blocks = [];

    	function select_block_type(ctx, dirty) {
    		if (/*queryResult*/ ctx[0].data.length === 1) return 0;
    		if (/*queryResult*/ ctx[0].data.length > 1) return 1;
    		return -1;
    	}

    	if (~(current_block_type_index = select_block_type(ctx))) {
    		if_block = if_blocks[current_block_type_index] = if_block_creators[current_block_type_index](ctx);
    	}

    	const block = {
    		c: function create() {
    			if (if_block) if_block.c();
    			if_block_anchor = empty();
    		},
    		l: function claim(nodes) {
    			throw new Error("options.hydrate only works if the component was compiled with the `hydratable: true` option");
    		},
    		m: function mount(target, anchor) {
    			if (~current_block_type_index) {
    				if_blocks[current_block_type_index].m(target, anchor);
    			}

    			insert_dev(target, if_block_anchor, anchor);
    			current = true;
    		},
    		p: function update(ctx, [dirty]) {
    			let previous_block_index = current_block_type_index;
    			current_block_type_index = select_block_type(ctx);

    			if (current_block_type_index === previous_block_index) {
    				if (~current_block_type_index) {
    					if_blocks[current_block_type_index].p(ctx, dirty);
    				}
    			} else {
    				if (if_block) {
    					group_outros();

    					transition_out(if_blocks[previous_block_index], 1, 1, () => {
    						if_blocks[previous_block_index] = null;
    					});

    					check_outros();
    				}

    				if (~current_block_type_index) {
    					if_block = if_blocks[current_block_type_index];

    					if (!if_block) {
    						if_block = if_blocks[current_block_type_index] = if_block_creators[current_block_type_index](ctx);
    						if_block.c();
    					} else {
    						if_block.p(ctx, dirty);
    					}

    					transition_in(if_block, 1);
    					if_block.m(if_block_anchor.parentNode, if_block_anchor);
    				} else {
    					if_block = null;
    				}
    			}
    		},
    		i: function intro(local) {
    			if (current) return;
    			transition_in(if_block);
    			current = true;
    		},
    		o: function outro(local) {
    			transition_out(if_block);
    			current = false;
    		},
    		d: function destroy(detaching) {
    			if (~current_block_type_index) {
    				if_blocks[current_block_type_index].d(detaching);
    			}

    			if (detaching) detach_dev(if_block_anchor);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_fragment$3.name,
    		type: "component",
    		source: "",
    		ctx
    	});

    	return block;
    }

    function instance$3($$self, $$props, $$invalidate) {
    	let { $$slots: slots = {}, $$scope } = $$props;
    	validate_slots('QueryResultDisplay', slots, []);
    	let { queryResult } = $$props;
    	const writable_props = ['queryResult'];

    	Object.keys($$props).forEach(key => {
    		if (!~writable_props.indexOf(key) && key.slice(0, 2) !== '$$' && key !== 'slot') console.warn(`<QueryResultDisplay> was created with unknown prop '${key}'`);
    	});

    	$$self.$$set = $$props => {
    		if ('queryResult' in $$props) $$invalidate(0, queryResult = $$props.queryResult);
    	};

    	$$self.$capture_state = () => ({ BigNumbers, TableDisplay, queryResult });

    	$$self.$inject_state = $$props => {
    		if ('queryResult' in $$props) $$invalidate(0, queryResult = $$props.queryResult);
    	};

    	if ($$props && "$$inject" in $$props) {
    		$$self.$inject_state($$props.$$inject);
    	}

    	return [queryResult];
    }

    class QueryResultDisplay extends SvelteComponentDev {
    	constructor(options) {
    		super(options);
    		init(this, options, instance$3, create_fragment$3, safe_not_equal, { queryResult: 0 });

    		dispatch_dev("SvelteRegisterComponent", {
    			component: this,
    			tagName: "QueryResultDisplay",
    			options,
    			id: create_fragment$3.name
    		});

    		const { ctx } = this.$$;
    		const props = options.props || {};

    		if (/*queryResult*/ ctx[0] === undefined && !('queryResult' in props)) {
    			console.warn("<QueryResultDisplay> was created without expected prop 'queryResult'");
    		}
    	}

    	get queryResult() {
    		throw new Error("<QueryResultDisplay>: Props cannot be read directly from the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}

    	set queryResult(value) {
    		throw new Error("<QueryResultDisplay>: Props cannot be set directly on the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}
    }

    /* src/components/QueryBuilder.svelte generated by Svelte v3.43.1 */

    const { console: console_1 } = globals;
    const file$1 = "src/components/QueryBuilder.svelte";

    // (71:4) {#if measures.length > 0}
    function create_if_block_1(ctx) {
    	let calculationselector;
    	let current;

    	calculationselector = new CalculationSelector({
    			props: {
    				title: "by",
    				placeholder: "find a dimension...",
    				calculations: /*dimensions*/ ctx[1],
    				availableCalculations: /*store*/ ctx[2].dimensions
    			},
    			$$inline: true
    		});

    	calculationselector.$on("addCalculation", /*addDimension*/ ctx[5]);
    	calculationselector.$on("removeCalculation", /*removeDimension*/ ctx[7]);

    	const block = {
    		c: function create() {
    			create_component(calculationselector.$$.fragment);
    		},
    		m: function mount(target, anchor) {
    			mount_component(calculationselector, target, anchor);
    			current = true;
    		},
    		p: function update(ctx, dirty) {
    			const calculationselector_changes = {};
    			if (dirty & /*dimensions*/ 2) calculationselector_changes.calculations = /*dimensions*/ ctx[1];
    			if (dirty & /*store*/ 4) calculationselector_changes.availableCalculations = /*store*/ ctx[2].dimensions;
    			calculationselector.$set(calculationselector_changes);
    		},
    		i: function intro(local) {
    			if (current) return;
    			transition_in(calculationselector.$$.fragment, local);
    			current = true;
    		},
    		o: function outro(local) {
    			transition_out(calculationselector.$$.fragment, local);
    			current = false;
    		},
    		d: function destroy(detaching) {
    			destroy_component(calculationselector, detaching);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_if_block_1.name,
    		type: "if",
    		source: "(71:4) {#if measures.length > 0}",
    		ctx
    	});

    	return block;
    }

    // (82:4) {#if measures.length > 0}
    function create_if_block(ctx) {
    	let queryresultdisplay;
    	let current;

    	queryresultdisplay = new QueryResultDisplay({
    			props: { queryResult: /*queryResult*/ ctx[3] },
    			$$inline: true
    		});

    	const block = {
    		c: function create() {
    			create_component(queryresultdisplay.$$.fragment);
    		},
    		m: function mount(target, anchor) {
    			mount_component(queryresultdisplay, target, anchor);
    			current = true;
    		},
    		p: function update(ctx, dirty) {
    			const queryresultdisplay_changes = {};
    			if (dirty & /*queryResult*/ 8) queryresultdisplay_changes.queryResult = /*queryResult*/ ctx[3];
    			queryresultdisplay.$set(queryresultdisplay_changes);
    		},
    		i: function intro(local) {
    			if (current) return;
    			transition_in(queryresultdisplay.$$.fragment, local);
    			current = true;
    		},
    		o: function outro(local) {
    			transition_out(queryresultdisplay.$$.fragment, local);
    			current = false;
    		},
    		d: function destroy(detaching) {
    			destroy_component(queryresultdisplay, detaching);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_if_block.name,
    		type: "if",
    		source: "(82:4) {#if measures.length > 0}",
    		ctx
    	});

    	return block;
    }

    function create_fragment$2(ctx) {
    	let div;
    	let calculationselector;
    	let t0;
    	let t1;
    	let current;

    	calculationselector = new CalculationSelector({
    			props: {
    				title: "Show me",
    				placeholder: "find a metric...",
    				calculations: /*measures*/ ctx[0],
    				availableCalculations: /*store*/ ctx[2].measures
    			},
    			$$inline: true
    		});

    	calculationselector.$on("addCalculation", /*addMeasure*/ ctx[4]);
    	calculationselector.$on("removeCalculation", /*removeMeasure*/ ctx[6]);
    	let if_block0 = /*measures*/ ctx[0].length > 0 && create_if_block_1(ctx);
    	let if_block1 = /*measures*/ ctx[0].length > 0 && create_if_block(ctx);

    	const block = {
    		c: function create() {
    			div = element("div");
    			create_component(calculationselector.$$.fragment);
    			t0 = space();
    			if (if_block0) if_block0.c();
    			t1 = space();
    			if (if_block1) if_block1.c();
    			add_location(div, file$1, 61, 0, 1855);
    		},
    		l: function claim(nodes) {
    			throw new Error("options.hydrate only works if the component was compiled with the `hydratable: true` option");
    		},
    		m: function mount(target, anchor) {
    			insert_dev(target, div, anchor);
    			mount_component(calculationselector, div, null);
    			append_dev(div, t0);
    			if (if_block0) if_block0.m(div, null);
    			append_dev(div, t1);
    			if (if_block1) if_block1.m(div, null);
    			current = true;
    		},
    		p: function update(ctx, [dirty]) {
    			const calculationselector_changes = {};
    			if (dirty & /*measures*/ 1) calculationselector_changes.calculations = /*measures*/ ctx[0];
    			if (dirty & /*store*/ 4) calculationselector_changes.availableCalculations = /*store*/ ctx[2].measures;
    			calculationselector.$set(calculationselector_changes);

    			if (/*measures*/ ctx[0].length > 0) {
    				if (if_block0) {
    					if_block0.p(ctx, dirty);

    					if (dirty & /*measures*/ 1) {
    						transition_in(if_block0, 1);
    					}
    				} else {
    					if_block0 = create_if_block_1(ctx);
    					if_block0.c();
    					transition_in(if_block0, 1);
    					if_block0.m(div, t1);
    				}
    			} else if (if_block0) {
    				group_outros();

    				transition_out(if_block0, 1, 1, () => {
    					if_block0 = null;
    				});

    				check_outros();
    			}

    			if (/*measures*/ ctx[0].length > 0) {
    				if (if_block1) {
    					if_block1.p(ctx, dirty);

    					if (dirty & /*measures*/ 1) {
    						transition_in(if_block1, 1);
    					}
    				} else {
    					if_block1 = create_if_block(ctx);
    					if_block1.c();
    					transition_in(if_block1, 1);
    					if_block1.m(div, null);
    				}
    			} else if (if_block1) {
    				group_outros();

    				transition_out(if_block1, 1, 1, () => {
    					if_block1 = null;
    				});

    				check_outros();
    			}
    		},
    		i: function intro(local) {
    			if (current) return;
    			transition_in(calculationselector.$$.fragment, local);
    			transition_in(if_block0);
    			transition_in(if_block1);
    			current = true;
    		},
    		o: function outro(local) {
    			transition_out(calculationselector.$$.fragment, local);
    			transition_out(if_block0);
    			transition_out(if_block1);
    			current = false;
    		},
    		d: function destroy(detaching) {
    			if (detaching) detach_dev(div);
    			destroy_component(calculationselector);
    			if (if_block0) if_block0.d();
    			if (if_block1) if_block1.d();
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_fragment$2.name,
    		type: "component",
    		source: "",
    		ctx
    	});

    	return block;
    }

    function instance$2($$self, $$props, $$invalidate) {
    	let query;
    	let { $$slots: slots = {}, $$scope } = $$props;
    	validate_slots('QueryBuilder', slots, []);
    	let store = { measures: [], dimensions: [] };
    	let measures = [];
    	let dimensions = [];
    	let queryResult = { data: [] };

    	const addCalculation = (arr, item) => {
    		const ids = arr.map(i => i.id);

    		if (ids.indexOf(item.id) === -1) {
    			return [...arr, item];
    		}

    		return arr;
    	};

    	const addMeasure = event => {
    		$$invalidate(0, measures = addCalculation(measures, event.detail.item));
    	};

    	const addDimension = event => {
    		$$invalidate(1, dimensions = addCalculation(dimensions, event.detail.item));
    	};

    	const removeMeasure = event => {
    		$$invalidate(0, measures = measures.filter(i => i.id !== event.detail.id));

    		if (measures.length === 0) {
    			getStore();
    		}
    	};

    	const removeDimension = event => {
    		$$invalidate(1, dimensions = dimensions.filter(i => i.id !== event.detail.id));
    	};

    	const runQuery = query => {
    		if (measures.length > 0) {
    			fetch("/api/query/", {
    				method: "POST",
    				headers: { "Content-Type": "application/json" },
    				body: JSON.stringify(query)
    			}).then(res => res.json()).then(data => {
    				$$invalidate(3, queryResult = data);
    				$$invalidate(2, store = data.metadata.store);
    			});
    		}
    	};

    	const getStore = () => {
    		fetch("/api/store/").then(res => res.json()).then(data => $$invalidate(2, store = data)).catch(err => console.error(err));
    	};

    	getStore();
    	const writable_props = [];

    	Object.keys($$props).forEach(key => {
    		if (!~writable_props.indexOf(key) && key.slice(0, 2) !== '$$' && key !== 'slot') console_1.warn(`<QueryBuilder> was created with unknown prop '${key}'`);
    	});

    	$$self.$capture_state = () => ({
    		CalculationSelector,
    		QueryResultDisplay,
    		store,
    		measures,
    		dimensions,
    		queryResult,
    		addCalculation,
    		addMeasure,
    		addDimension,
    		removeMeasure,
    		removeDimension,
    		runQuery,
    		getStore,
    		query
    	});

    	$$self.$inject_state = $$props => {
    		if ('store' in $$props) $$invalidate(2, store = $$props.store);
    		if ('measures' in $$props) $$invalidate(0, measures = $$props.measures);
    		if ('dimensions' in $$props) $$invalidate(1, dimensions = $$props.dimensions);
    		if ('queryResult' in $$props) $$invalidate(3, queryResult = $$props.queryResult);
    		if ('query' in $$props) $$invalidate(8, query = $$props.query);
    	};

    	if ($$props && "$$inject" in $$props) {
    		$$self.$inject_state($$props.$$inject);
    	}

    	$$self.$$.update = () => {
    		if ($$self.$$.dirty & /*measures, dimensions*/ 3) {
    			$$invalidate(8, query = {
    				measures: measures.map(i => i.id),
    				dimensions: dimensions.map(i => i.id)
    			});
    		}

    		if ($$self.$$.dirty & /*query*/ 256) {
    			runQuery(query);
    		}
    	};

    	return [
    		measures,
    		dimensions,
    		store,
    		queryResult,
    		addMeasure,
    		addDimension,
    		removeMeasure,
    		removeDimension,
    		query
    	];
    }

    class QueryBuilder extends SvelteComponentDev {
    	constructor(options) {
    		super(options);
    		init(this, options, instance$2, create_fragment$2, safe_not_equal, {});

    		dispatch_dev("SvelteRegisterComponent", {
    			component: this,
    			tagName: "QueryBuilder",
    			options,
    			id: create_fragment$2.name
    		});
    	}
    }

    /* src/pages/Components.svelte generated by Svelte v3.43.1 */
    const file = "src/pages/Components.svelte";

    function create_fragment$1(ctx) {
    	let div;
    	let querybuilder;
    	let current;
    	querybuilder = new QueryBuilder({ $$inline: true });

    	const block = {
    		c: function create() {
    			div = element("div");
    			create_component(querybuilder.$$.fragment);
    			attr_dev(div, "class", "container svelte-t5466c");
    			add_location(div, file, 13, 0, 571);
    		},
    		l: function claim(nodes) {
    			throw new Error("options.hydrate only works if the component was compiled with the `hydratable: true` option");
    		},
    		m: function mount(target, anchor) {
    			insert_dev(target, div, anchor);
    			mount_component(querybuilder, div, null);
    			current = true;
    		},
    		p: noop,
    		i: function intro(local) {
    			if (current) return;
    			transition_in(querybuilder.$$.fragment, local);
    			current = true;
    		},
    		o: function outro(local) {
    			transition_out(querybuilder.$$.fragment, local);
    			current = false;
    		},
    		d: function destroy(detaching) {
    			if (detaching) detach_dev(div);
    			destroy_component(querybuilder);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_fragment$1.name,
    		type: "component",
    		source: "",
    		ctx
    	});

    	return block;
    }

    function instance$1($$self, $$props, $$invalidate) {
    	let { $$slots: slots = {}, $$scope } = $$props;
    	validate_slots('Components', slots, []);
    	let name = "Number of Tracks";
    	let description = "Total number of tracks in our media library. Note that there are different media types included, not only music. Use this measure to explore what can possible be sold here. Can be split up by various musical parameters: genre, artist, album. Has no connection to sales.";
    	let expr = "count()";
    	let calculations = [{ id: 1, name, description, expr }, { id: 2, name, description, expr }];
    	const writable_props = [];

    	Object.keys($$props).forEach(key => {
    		if (!~writable_props.indexOf(key) && key.slice(0, 2) !== '$$' && key !== 'slot') console.warn(`<Components> was created with unknown prop '${key}'`);
    	});

    	$$self.$capture_state = () => ({
    		QueryBuilder,
    		name,
    		description,
    		expr,
    		calculations
    	});

    	$$self.$inject_state = $$props => {
    		if ('name' in $$props) name = $$props.name;
    		if ('description' in $$props) description = $$props.description;
    		if ('expr' in $$props) expr = $$props.expr;
    		if ('calculations' in $$props) calculations = $$props.calculations;
    	};

    	if ($$props && "$$inject" in $$props) {
    		$$self.$inject_state($$props.$$inject);
    	}

    	return [];
    }

    class Components extends SvelteComponentDev {
    	constructor(options) {
    		super(options);
    		init(this, options, instance$1, create_fragment$1, safe_not_equal, {});

    		dispatch_dev("SvelteRegisterComponent", {
    			component: this,
    			tagName: "Components",
    			options,
    			id: create_fragment$1.name
    		});
    	}
    }

    /* src/App.svelte generated by Svelte v3.43.1 */

    function create_fragment(ctx) {
    	let components;
    	let current;
    	components = new Components({ $$inline: true });

    	const block = {
    		c: function create() {
    			create_component(components.$$.fragment);
    		},
    		l: function claim(nodes) {
    			throw new Error("options.hydrate only works if the component was compiled with the `hydratable: true` option");
    		},
    		m: function mount(target, anchor) {
    			mount_component(components, target, anchor);
    			current = true;
    		},
    		p: noop,
    		i: function intro(local) {
    			if (current) return;
    			transition_in(components.$$.fragment, local);
    			current = true;
    		},
    		o: function outro(local) {
    			transition_out(components.$$.fragment, local);
    			current = false;
    		},
    		d: function destroy(detaching) {
    			destroy_component(components, detaching);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_fragment.name,
    		type: "component",
    		source: "",
    		ctx
    	});

    	return block;
    }

    function instance($$self, $$props, $$invalidate) {
    	let { $$slots: slots = {}, $$scope } = $$props;
    	validate_slots('App', slots, []);
    	const writable_props = [];

    	Object.keys($$props).forEach(key => {
    		if (!~writable_props.indexOf(key) && key.slice(0, 2) !== '$$' && key !== 'slot') console.warn(`<App> was created with unknown prop '${key}'`);
    	});

    	$$self.$capture_state = () => ({ Components });
    	return [];
    }

    class App extends SvelteComponentDev {
    	constructor(options) {
    		super(options);
    		init(this, options, instance, create_fragment, safe_not_equal, {});

    		dispatch_dev("SvelteRegisterComponent", {
    			component: this,
    			tagName: "App",
    			options,
    			id: create_fragment.name
    		});
    	}
    }

    const app = new App({
    	target: document.body,
    });

    return app;

})();
//# sourceMappingURL=bundle.js.map
