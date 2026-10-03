const vm = require("node:vm"); for (let i = 0; i < 10; ++i) { vm.runInNewContext("({answer: 42}).answer"); gc(); } console.log("Node GC control passed");
