import{d as e,n as t,p as n,t as r,u as i}from"./createLucideIcon-C5DqQxtk.js";import{f as a,l as o,t as s}from"./UI-MRe4HNA3.js";import{t as c}from"./sparkles-wFd8Uc0T.js";import{l,n as u,s as d,t as ee,u as f}from"./index-Dxnqs4Ks.js";var p=r(`clock`,[[`circle`,{cx:`12`,cy:`12`,r:`10`,key:`1mglay`}],[`path`,{d:`M12 6v6l4 2`,key:`mmk7yg`}]]),m=r(`flame`,[[`path`,{d:`M12 3q1 4 4 6.5t3 5.5a1 1 0 0 1-14 0 5 5 0 0 1 1-3 1 1 0 0 0 5 0c0-2-1.5-3-1.5-5q0-2 2.5-4`,key:`1slcih`}]]),h=r(`wind`,[[`path`,{d:`M12.8 19.6A2 2 0 1 0 14 16H2`,key:`148xed`}],[`path`,{d:`M17.5 8a2.5 2.5 0 1 1 2 4H2`,key:`1u4tom`}],[`path`,{d:`M9.8 4.4A2 2 0 1 1 11 8H2`,key:`75valh`}]]),g=n(e(),1),_={data:``},v=e=>{if(typeof window==`object`){let t=(e?e.querySelector(`#_goober`):window._goober)||Object.assign(document.createElement(`style`),{innerHTML:` `,id:`_goober`});return t.nonce=window.__nonce__,t.parentNode||(e||document.head).appendChild(t),t.firstChild}return e||_},y=/(?:([\u0080-\uFFFF\w-%@]+) *:? *([^{;]+?);|([^;}{]*?) *{)|(}\s*)/g,te=/\/\*[^]*?\*\/|  +/g,b=/\n+/g,x=(e,t)=>{let n=``,r=``,i=``;for(let a in e){let o=e[a];a[0]==`@`?a[1]==`i`?n=a+` `+o+`;`:r+=a[1]==`f`?x(o,a):a+`{`+x(o,a[1]==`k`?``:t)+`}`:typeof o==`object`?r+=x(o,t?t.replace(/([^,])+/g,e=>a.replace(/([^,]*:\S+\([^)]*\))|([^,])+/g,t=>/&/.test(t)?t.replace(/&/g,e):e?e+` `+t:t)):a):o!=null&&(a=/^--/.test(a)?a:a.replace(/[A-Z]/g,`-$&`).toLowerCase(),i+=x.p?x.p(a,o):a+`:`+o+`;`)}return n+(t&&i?t+`{`+i+`}`:i)+r},S={},C=e=>{if(typeof e==`object`){let t=``;for(let n in e)t+=n+C(e[n]);return t}return e},w=(e,t,n,r,i)=>{let a=C(e),o=S[a]||(S[a]=(e=>{let t=0,n=11;for(;t<e.length;)n=101*n+e.charCodeAt(t++)>>>0;return`go`+n})(a));if(!S[o]){let t=a===e?(e=>{let t,n,r=[{}];for(;t=y.exec(e.replace(te,``));)t[4]?r.shift():t[3]?(n=t[3].replace(b,` `).trim(),r.unshift(r[0][n]=r[0][n]||{})):r[0][t[1]]=t[2].replace(b,` `).trim();return r[0]})(e):e;S[o]=x(i?{[`@keyframes `+o]:t}:t,n?``:`.`+o)}let s=n&&S.g?S.g:null;return n&&(S.g=S[o]),((e,t,n,r)=>{r?t.data=t.data.replace(r,e):t.data.indexOf(e)===-1&&(t.data=n?e+t.data:t.data+e)})(S[o],t,r,s),o},T=(e,t,n)=>e.reduce((e,r,i)=>{let a=t[i];if(a&&a.call){let e=a(n),t=e&&e.props&&e.props.className||/^go/.test(e)&&e;a=t?`.`+t:e&&typeof e==`object`?e.props?``:x(e,``):!1===e?``:e}return e+r+(a??``)},``);function E(e){let t=this||{},n=e.call?e(t.p):e;return w(n.unshift?n.raw?T(n,[].slice.call(arguments,1),t.p):n.reduce((e,n)=>Object.assign(e,n&&n.call?n(t.p):n),{}):n,v(t.target),t.g,t.o,t.k)}var D,O,k;E.bind({g:1});var A=E.bind({k:1});function j(e,t,n,r){x.p=t,D=e,O=n,k=r}function M(e,t){let n=this||{};return function(){let r=arguments;function i(a,o){let s=Object.assign({},a),c=s.className||i.className;n.p=Object.assign({theme:O&&O()},s),n.o=/ *go\d+/.test(c),s.className=E.apply(n,r)+(c?` `+c:``),t&&(s.ref=o);let l=e;return e[0]&&(l=s.as||e,delete s.as),k&&l[0]&&k(s),D(l,s)}return t?t(i):i}}var N=e=>typeof e==`function`,P=(e,t)=>N(e)?e(t):e,F=(()=>{let e=0;return()=>(++e).toString()})(),I=(()=>{let e;return()=>{if(e===void 0&&typeof window<`u`){let t=matchMedia(`(prefers-reduced-motion: reduce)`);e=!t||t.matches}return e}})(),ne=20,L=`default`,R=(e,t)=>{let{toastLimit:n}=e.settings;switch(t.type){case 0:return{...e,toasts:[t.toast,...e.toasts].slice(0,n)};case 1:return{...e,toasts:e.toasts.map(e=>e.id===t.toast.id?{...e,...t.toast}:e)};case 2:let{toast:r}=t;return R(e,{type:e.toasts.find(e=>e.id===r.id)?1:0,toast:r});case 3:let{toastId:i}=t;return{...e,toasts:e.toasts.map(e=>e.id===i||i===void 0?{...e,dismissed:!0,visible:!1}:e)};case 4:return t.toastId===void 0?{...e,toasts:[]}:{...e,toasts:e.toasts.filter(e=>e.id!==t.toastId)};case 5:return{...e,pausedAt:t.time};case 6:let a=t.time-(e.pausedAt||0);return{...e,pausedAt:void 0,toasts:e.toasts.map(e=>({...e,pauseDuration:e.pauseDuration+a}))}}},re=[],ie={toasts:[],pausedAt:void 0,settings:{toastLimit:ne}},z={},B=(e,t=L)=>{z[t]=R(z[t]||ie,e),re.forEach(([e,n])=>{e===t&&n(z[t])})},V=e=>Object.keys(z).forEach(t=>B(e,t)),H=e=>Object.keys(z).find(t=>z[t].toasts.some(t=>t.id===e)),U=(e=L)=>t=>{B(t,e)},W=(e,t=`blank`,n)=>({createdAt:Date.now(),visible:!0,dismissed:!1,type:t,ariaProps:{role:`status`,"aria-live":`polite`},message:e,pauseDuration:0,...n,id:n?.id||F()}),G=e=>(t,n)=>{let r=W(t,e,n);return U(r.toasterId||H(r.id))({type:2,toast:r}),r.id},K=(e,t)=>G(`blank`)(e,t);K.error=G(`error`),K.success=G(`success`),K.loading=G(`loading`),K.custom=G(`custom`),K.dismiss=(e,t)=>{let n={type:3,toastId:e};t?U(t)(n):V(n)},K.dismissAll=e=>K.dismiss(void 0,e),K.remove=(e,t)=>{let n={type:4,toastId:e};t?U(t)(n):V(n)},K.removeAll=e=>K.remove(void 0,e),K.promise=(e,t,n)=>{let r=K.loading(t.loading,{...n,...n?.loading});return typeof e==`function`&&(e=e()),e.then(e=>{let i=t.success?P(t.success,e):void 0;return i?K.success(i,{id:r,...n,...n?.success}):K.dismiss(r),e}).catch(e=>{let i=t.error?P(t.error,e):void 0;i?K.error(i,{id:r,...n,...n?.error}):K.dismiss(r)}),e};var q=A`
from {
  transform: scale(0) rotate(45deg);
	opacity: 0;
}
to {
 transform: scale(1) rotate(45deg);
  opacity: 1;
}`,J=A`
from {
  transform: scale(0);
  opacity: 0;
}
to {
  transform: scale(1);
  opacity: 1;
}`,Y=A`
from {
  transform: scale(0) rotate(90deg);
	opacity: 0;
}
to {
  transform: scale(1) rotate(90deg);
	opacity: 1;
}`,ae=M(`div`)`
  width: 20px;
  opacity: 0;
  height: 20px;
  border-radius: 10px;
  background: ${e=>e.primary||`#ff4b4b`};
  position: relative;
  transform: rotate(45deg);

  animation: ${q} 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)
    forwards;
  animation-delay: 100ms;

  &:after,
  &:before {
    content: '';
    animation: ${J} 0.15s ease-out forwards;
    animation-delay: 150ms;
    position: absolute;
    border-radius: 3px;
    opacity: 0;
    background: ${e=>e.secondary||`#fff`};
    bottom: 9px;
    left: 4px;
    height: 2px;
    width: 12px;
  }

  &:before {
    animation: ${Y} 0.15s ease-out forwards;
    animation-delay: 180ms;
    transform: rotate(90deg);
  }
`,oe=A`
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
`,se=M(`div`)`
  width: 12px;
  height: 12px;
  box-sizing: border-box;
  border: 2px solid;
  border-radius: 100%;
  border-color: ${e=>e.secondary||`#e0e0e0`};
  border-right-color: ${e=>e.primary||`#616161`};
  animation: ${oe} 1s linear infinite;
`,ce=A`
from {
  transform: scale(0) rotate(45deg);
	opacity: 0;
}
to {
  transform: scale(1) rotate(45deg);
	opacity: 1;
}`,le=A`
0% {
	height: 0;
	width: 0;
	opacity: 0;
}
40% {
  height: 0;
	width: 6px;
	opacity: 1;
}
100% {
  opacity: 1;
  height: 10px;
}`,ue=M(`div`)`
  width: 20px;
  opacity: 0;
  height: 20px;
  border-radius: 10px;
  background: ${e=>e.primary||`#61d345`};
  position: relative;
  transform: rotate(45deg);

  animation: ${ce} 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)
    forwards;
  animation-delay: 100ms;
  &:after {
    content: '';
    box-sizing: border-box;
    animation: ${le} 0.2s ease-out forwards;
    opacity: 0;
    animation-delay: 200ms;
    position: absolute;
    border-right: 2px solid;
    border-bottom: 2px solid;
    border-color: ${e=>e.secondary||`#fff`};
    bottom: 6px;
    left: 6px;
    height: 10px;
    width: 6px;
  }
`,de=M(`div`)`
  position: absolute;
`,fe=M(`div`)`
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  min-width: 20px;
  min-height: 20px;
`,pe=A`
from {
  transform: scale(0.6);
  opacity: 0.4;
}
to {
  transform: scale(1);
  opacity: 1;
}`,me=M(`div`)`
  position: relative;
  transform: scale(0.6);
  opacity: 0.4;
  min-width: 20px;
  animation: ${pe} 0.3s 0.12s cubic-bezier(0.175, 0.885, 0.32, 1.275)
    forwards;
`,he=({toast:e})=>{let{icon:t,type:n,iconTheme:r}=e;return t===void 0?n===`blank`?null:g.createElement(fe,null,g.createElement(se,{...r}),n!==`loading`&&g.createElement(de,null,n===`error`?g.createElement(ae,{...r}):g.createElement(ue,{...r}))):typeof t==`string`?g.createElement(me,null,t):t},ge=e=>`
0% {transform: translate3d(0,${e*-200}%,0) scale(.6); opacity:.5;}
100% {transform: translate3d(0,0,0) scale(1); opacity:1;}
`,_e=e=>`
0% {transform: translate3d(0,0,-1px) scale(1); opacity:1;}
100% {transform: translate3d(0,${e*-150}%,-1px) scale(.6); opacity:0;}
`,ve=`0%{opacity:0;} 100%{opacity:1;}`,ye=`0%{opacity:1;} 100%{opacity:0;}`,be=M(`div`)`
  display: flex;
  align-items: center;
  background: #fff;
  color: #363636;
  line-height: 1.3;
  will-change: transform;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1), 0 3px 3px rgba(0, 0, 0, 0.05);
  max-width: 350px;
  pointer-events: auto;
  padding: 8px 10px;
  border-radius: 8px;
`,xe=M(`div`)`
  display: flex;
  justify-content: center;
  margin: 4px 10px;
  color: inherit;
  flex: 1 1 auto;
  white-space: pre-line;
`,X=(e,t)=>{let n=e.includes(`top`)?1:-1,[r,i]=I()?[ve,ye]:[ge(n),_e(n)];return{animation:t?`${A(r)} 0.35s cubic-bezier(.21,1.02,.73,1) forwards`:`${A(i)} 0.4s forwards cubic-bezier(.06,.71,.55,1)`}};g.memo(({toast:e,position:t,style:n,children:r})=>{let i=e.height?X(e.position||t||`top-center`,e.visible):{opacity:0},a=g.createElement(he,{toast:e}),o=g.createElement(xe,{...e.ariaProps},P(e.message,e));return g.createElement(be,{className:e.className,style:{...i,...n,...e.style}},typeof r==`function`?r({icon:a,message:o}):g.createElement(g.Fragment,null,a,o))}),j(g.createElement),E`
  z-index: 9999;
  > * {
    pointer-events: auto;
  }
`;var Z=i(),Q={common:{color:`text-slate-400`,bg:`bg-slate-400/10`,border:`border-slate-400/20`},gold:{color:`text-brand-accent`,bg:`bg-brand-accent/10`,border:`border-brand-accent/20`},void:{color:`text-purple-500`,bg:`bg-purple-500/10`,border:`border-purple-500/20`}},Se={Caregiver:d,Scavenger:c,Pyromaniac:m,Swift:h},Ce=({pet:e,isActive:t,onSelect:n})=>{let r=Se[e.ability]||u;return(0,Z.jsxs)(`button`,{onClick:n,className:`glass-panel p-4 rounded-3xl border text-left relative transition-all active:scale-95 ${t?`border-brand-neon/40 ring-1 ring-brand-neon/20 shadow-lg shadow-brand-neon/5`:`border-white/5 opacity-60 grayscale hover:opacity-100`}`,children:[(0,Z.jsxs)(`div`,{className:`flex justify-between items-start mb-4`,children:[(0,Z.jsx)(`div`,{className:`w-10 h-10 rounded-xl flex items-center justify-center ${t?`bg-brand-neon/10 text-brand-neon`:`bg-slate-800 text-slate-500`}`,children:(0,Z.jsx)(r,{size:20})}),t&&(0,Z.jsx)(`div`,{className:`bg-brand-neon text-brand-midnight text-[8px] font-black uppercase px-1.5 py-0.5 rounded tracking-tighter shadow-lg`,children:`Active Squad`})]}),(0,Z.jsx)(`h4`,{className:`text-[13px] font-black uppercase tracking-tight text-white mb-0.5`,children:e.name}),(0,Z.jsx)(`p`,{className:`text-[9px] font-bold text-slate-400 uppercase tracking-widest mb-3`,children:e.type||`Nanotech Support`}),(0,Z.jsxs)(`div`,{className:`pt-3 border-t border-white/5 space-y-1`,children:[(0,Z.jsxs)(`div`,{className:`flex items-center space-x-1.5 text-brand-neon`,children:[(0,Z.jsx)(r,{size:10}),(0,Z.jsx)(`span`,{className:`text-[9px] font-black uppercase tracking-widest`,children:e.ability||`Standard`})]}),(0,Z.jsx)(`p`,{className:`text-[8px] leading-tight text-slate-500 font-medium line-clamp-2`,children:e.desc||`Standard surveillance and support unit.`})]})]})},we=({egg:e,onIncubate:t,onHatch:n,loading:r})=>{let i=Q[e.tier]||Q.common,a=e.status===`incubating`,[o,s]=(0,g.useState)(``);(0,g.useEffect)(()=>{if(!a||!e.hatch_time)return;let t=()=>{let t=new Date,n=new Date(e.hatch_time)-t;if(n<=0)s(`READY`);else{let e=Math.floor(n/6e4),t=Math.floor(n%6e4/1e3);s(`${e}:${t<10?`0`:``}${t}`)}};t();let n=setInterval(t,1e3);return()=>clearInterval(n)},[e.hatch_time,a]);let c=o===`READY`;return(0,Z.jsxs)(`div`,{className:`glass-panel p-5 rounded-3xl border ${i.border} flex items-center space-x-4 relative overflow-hidden group`,children:[(0,Z.jsx)(`div`,{className:`w-14 h-14 rounded-2xl ${i.bg} ${i.color} flex items-center justify-center relative z-10`,children:(0,Z.jsx)(f,{size:28,className:a?`animate-bounce`:``})}),(0,Z.jsxs)(`div`,{className:`flex-1 relative z-10`,children:[(0,Z.jsx)(`h4`,{className:`text-[14px] font-black uppercase tracking-tight text-white mb-0.5`,children:e.name||`Unknown Pod`}),(0,Z.jsxs)(`div`,{className:`flex items-center space-x-2`,children:[(0,Z.jsxs)(`span`,{className:`text-[10px] font-bold uppercase tracking-widest ${i.color}`,children:[e.tier,` System`]}),(0,Z.jsx)(`div`,{className:`w-1 h-1 rounded-full bg-slate-700`}),(0,Z.jsx)(`span`,{className:`text-[10px] font-bold uppercase tracking-widest text-slate-500`,children:e.status})]})]}),(0,Z.jsx)(`div`,{className:`relative z-10`,children:e.status===`fresh`||!e.status?(0,Z.jsx)(`button`,{onClick:t,disabled:r,className:`bg-white text-brand-midnight text-[10px] font-black uppercase px-6 py-3 rounded-xl tracking-widest active:scale-95 transition-all shadow-lg`,children:`Initiate`}):(0,Z.jsxs)(`div`,{className:`flex flex-col items-end`,children:[(0,Z.jsxs)(`div`,{className:`flex items-center space-x-2 mb-1`,children:[(0,Z.jsx)(p,{size:12,className:`text-brand-neon`}),(0,Z.jsx)(`span`,{className:`text-[12px] font-black font-mono text-brand-neon`,children:o})]}),c&&(0,Z.jsx)(`button`,{onClick:n,disabled:r,className:`bg-brand-neon text-brand-midnight text-[10px] font-black uppercase px-6 py-2.5 rounded-xl tracking-widest animate-pulse shadow-[0_0_15px_rgba(0,255,255,0.3)]`,children:`Hatch`})]})}),(0,Z.jsx)(`div`,{className:`absolute right-0 bottom-0 translate-x-1/4 translate-y-1/4 opacity-5 group-hover:opacity-10 transition-opacity`,children:(0,Z.jsx)(f,{size:120})})]})},$=({icon:e,message:t})=>(0,Z.jsxs)(`div`,{className:`glass-panel p-12 rounded-3xl border border-white/5 text-center flex flex-col items-center opacity-40`,children:[(0,Z.jsx)(e,{size:40,className:`text-slate-800 mb-4`}),(0,Z.jsx)(`p`,{className:`text-slate-500 text-[10px] font-bold uppercase tracking-widest leading-relaxed max-w-[200px]`,children:t})]}),Te=()=>{let{user:e,loading:n,refreshUser:r}=ee(),[i,c]=(0,g.useState)(!1),[d,p]=(0,g.useState)(`eggs`),[m,h]=(0,g.useState)(null),_=async e=>{c(!0);try{await o(`/eggs/incubate/${e}`,{method:`POST`}),K.success(`Incubation Matrix Active`),await r()}catch(e){K.error(e.message||`Calibration failure`)}finally{c(!1)}},v=async e=>{c(!0);try{let t=await o(`/eggs/hatch/${e}`,{method:`POST`});t.status===`success`?(h(t.character),K.success(`Lifeform Detected`)):K.error(t.message||`Incubation Failure`),await r()}catch(e){K.error(e.message||`Hatch protocol interrupted`)}finally{c(!1)}};(0,g.useEffect)(()=>{if(m){let e=document.querySelector(`.app-scroller`);return e&&(e.style.overflow=`hidden`),()=>{let e=document.querySelector(`.app-scroller`);e&&(e.style.overflow=`auto`)}}},[m]);let y=async e=>{try{await o(`/pets/set_active/${e}`,{method:`POST`}),K.success(`${e} Synced to Core`),await r()}catch(e){K.error(e.message||`Sync failed`)}};return n?(0,Z.jsxs)(`div`,{className:`p-10 flex flex-col items-center justify-center min-h-[60vh]`,children:[(0,Z.jsx)(l,{className:`animate-spin text-brand-neon/20 mb-4`,size:32}),(0,Z.jsx)(`p`,{className:`text-slate-600 text-[10px] font-black uppercase tracking-widest`,children:`Scanning Pod Signatures...`})]}):e?(0,Z.jsxs)(`div`,{className:`pb-8 pt-6 px-4 max-w-lg mx-auto`,children:[(0,Z.jsxs)(`section`,{className:`mb-8 text-center relative`,children:[(0,Z.jsx)(`div`,{className:`absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 w-32 h-32 bg-brand-neon/5 blur-[60px] rounded-full pointer-events-none`}),(0,Z.jsx)(`h1`,{className:`text-2xl font-black uppercase tracking-[0.3em] mb-2 text-white`,children:`Hatchery`}),(0,Z.jsx)(`p`,{className:`text-[10px] font-bold text-slate-500 uppercase tracking-widest opacity-60`,children:`Nanobotic Lifeform Management`})]}),(0,Z.jsx)(`div`,{className:`flex bg-white/5 p-1 rounded-2xl mb-8 border border-white/5`,children:[`eggs`,`pets`].map(t=>(0,Z.jsx)(`button`,{onClick:()=>p(t),className:`flex-1 py-3 rounded-xl text-[11px] font-black uppercase tracking-widest transition-all ${d===t?`bg-white/10 text-white shadow-lg border border-white/5`:`text-slate-500 hover:text-slate-300`}`,children:(0,Z.jsxs)(`div`,{className:`flex items-center justify-center space-x-2`,children:[t===`eggs`?(0,Z.jsx)(f,{size:14}):(0,Z.jsx)(u,{size:14}),(0,Z.jsx)(`span`,{children:t===`eggs`?`PODS (${e.eggs?.length||0})`:`PET SQUAD`})]})},t))}),(0,Z.jsx)(a,{mode:`wait`,children:d===`eggs`?(0,Z.jsx)(t.section,{initial:{opacity:0,scale:.95},animate:{opacity:1,scale:1},exit:{opacity:0,scale:.95},className:`space-y-4`,children:e.eggs&&e.eggs.length>0?e.eggs.map(e=>(0,Z.jsx)(we,{egg:e,onIncubate:()=>_(e.id),onHatch:()=>v(e.id),loading:i},e.id)):(0,Z.jsx)($,{icon:f,message:`No pods detected. High-tier eggs are generated via the Elite Pass.`})},`egg-grid`):(0,Z.jsx)(t.section,{initial:{opacity:0,scale:.95},animate:{opacity:1,scale:1},exit:{opacity:0,scale:.95},className:`grid grid-cols-2 gap-3`,children:e.pets&&e.pets.length>0?e.pets.map(t=>(0,Z.jsx)(Ce,{pet:t,isActive:e.current_pet===t.name,onSelect:()=>y(t.name)},t.name)):(0,Z.jsx)(`div`,{className:`col-span-2`,children:(0,Z.jsx)($,{icon:u,message:`No companions active. Purchase support units in the Shop.`})})},`pet-grid`)}),(0,Z.jsx)(a,{children:m&&(0,Z.jsx)(`div`,{className:`fixed inset-0 z-[100] flex items-center justify-center p-6 bg-brand-midnight/90 backdrop-blur-xl`,children:(0,Z.jsxs)(t.div,{initial:{scale:.8,opacity:0},animate:{scale:1,opacity:1},className:`w-full max-w-sm`,children:[(0,Z.jsxs)(`div`,{className:`text-center mb-8`,children:[(0,Z.jsx)(`h3`,{className:`text-brand-neon font-black uppercase tracking-[0.4em] text-sm mb-2`,children:`Lifeform Detected`}),(0,Z.jsx)(`p`,{className:`text-[10px] text-slate-500 font-bold uppercase tracking-widest`,children:`Integrating personality to matrix`})]}),(0,Z.jsxs)(`div`,{className:`relative`,children:[(0,Z.jsx)(`div`,{className:`absolute -inset-10 bg-brand-neon/10 blur-[100px] rounded-full animate-pulse`}),(0,Z.jsx)(s,{character:m})]}),(0,Z.jsx)(`button`,{onClick:()=>h(null),className:`w-full mt-12 py-5 rounded-2xl bg-white text-brand-midnight font-black uppercase text-[11px] tracking-[0.3em] active:scale-95 transition-all shadow-xl`,children:`Close Portal`})]})})})]}):null};export{Te as Hatchery};