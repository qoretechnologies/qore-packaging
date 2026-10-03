function app(a, b) { for (const x of b) { a.push(x); } return a; }
function leb(n) {
    const out = [];
    do { let b = n & 0x7f; n >>>= 7; if (n) { b |= 0x80; } out.push(b); } while (n);
    return out;
}
function section(id, bytes) { return app(app([id], leb(bytes.length)), bytes); }
function vec(items) { const out = leb(items.length); for (const i of items) { app(out, i); } return out; }
// returns a module with 'nfuncs' functions of type () -> i32, each summing 'nops' constants
function makeModule(nfuncs, nops) {
    const body = [0];
    for (let i = 0; i < nops; ++i) { body.push(0x41, 0x01); }
    for (let i = 1; i < nops; ++i) { body.push(0x6a); }
    body.push(0x0b);
    const fbody = app(leb(body.length), body);
    const bytes = [0x00, 0x61, 0x73, 0x6d, 0x01, 0x00, 0x00, 0x00];
    app(bytes, section(1, vec([[0x60, 0x00, 0x01, 0x7f]])));
    app(bytes, section(3, vec(Array(nfuncs).fill([0]))));
    const code = leb(nfuncs);
    for (let i = 0; i < nfuncs; ++i) { app(code, fbody); }
    app(bytes, section(10, code));
    return new Uint8Array(bytes);
}
const mod = makeModule(2000, 400);
// an invalid module: the last function body is truncated, so validation fails in the background
const badMod = mod.slice(0, mod.length - 2);
// starts compiling the module asynchronously; returns a promise that resolves with the number of exports of the
// compiled module or with the name of the error class if the compilation fails
globalThis.startCompile = function(bad) {
    return WebAssembly.compile(bad ? badMod : mod).then((m) => WebAssembly.Module.exports(m).length,
        (e) => e.constructor.name);
};
Promise.all([startCompile(false), startCompile(true)]).then(([good,bad]) => { if(good !== 0 || bad !== "CompileError") throw new Error("bad result"); console.log("valid and malformed Wasm controls passed"); });
