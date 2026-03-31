import{a as e,c as t,d as n,i as r,l as i,n as a,o,p as s,r as c,s as l,t as u,u as d}from"./createLucideIcon-C5DqQxtk.js";var f=s(n(),1);function p(e,t){if(typeof e==`function`)return e(t);e!=null&&(e.current=t)}function m(...e){return t=>{let n=!1,r=e.map(e=>{let r=p(e,t);return!n&&typeof r==`function`&&(n=!0),r});if(n)return()=>{for(let t=0;t<r.length;t++){let n=r[t];typeof n==`function`?n():p(e[t],null)}}}}function h(...e){return f.useCallback(m(...e),e)}var g=d(),_=class extends f.Component{getSnapshotBeforeUpdate(t){let n=this.props.childRef.current;if(e(n)&&t.isPresent&&!this.props.isPresent&&this.props.pop!==!1){let t=n.offsetParent,r=e(t)&&t.offsetWidth||0,i=e(t)&&t.offsetHeight||0,a=getComputedStyle(n),o=this.props.sizeRef.current;o.height=parseFloat(a.height),o.width=parseFloat(a.width),o.top=n.offsetTop,o.left=n.offsetLeft,o.right=r-o.width-o.left,o.bottom=i-o.height-o.top}return null}componentDidUpdate(){}render(){return this.props.children}};function v({children:e,isPresent:t,anchorX:n,anchorY:i,root:a,pop:o}){let s=(0,f.useId)(),c=(0,f.useRef)(null),l=(0,f.useRef)({width:0,height:0,top:0,left:0,right:0,bottom:0}),{nonce:u}=(0,f.useContext)(r),d=h(c,e.props?.ref??e?.ref);return(0,f.useInsertionEffect)(()=>{let{width:e,height:r,top:d,left:f,right:p,bottom:m}=l.current;if(t||o===!1||!c.current||!e||!r)return;let h=n===`left`?`left: ${f}`:`right: ${p}`,g=i===`bottom`?`bottom: ${m}`:`top: ${d}`;c.current.dataset.motionPopId=s;let _=document.createElement(`style`);u&&(_.nonce=u);let v=a??document.head;return v.appendChild(_),_.sheet&&_.sheet.insertRule(`
          [data-motion-pop-id="${s}"] {
            position: absolute !important;
            width: ${e}px !important;
            height: ${r}px !important;
            ${h}px !important;
            ${g}px !important;
          }
        `),()=>{c.current?.removeAttribute(`data-motion-pop-id`),v.contains(_)&&v.removeChild(_)}},[t]),(0,g.jsx)(_,{isPresent:t,childRef:c,sizeRef:l,pop:o,children:o===!1?e:f.cloneElement(e,{ref:d})})}var ee=({children:e,initial:n,isPresent:r,onExitComplete:i,custom:a,presenceAffectsLayout:s,mode:c,anchorX:l,anchorY:u,root:d})=>{let p=t(y),m=(0,f.useId)(),h=!0,_=(0,f.useMemo)(()=>(h=!1,{id:m,initial:n,isPresent:r,custom:a,onExitComplete:e=>{p.set(e,!0);for(let e of p.values())if(!e)return;i&&i()},register:e=>(p.set(e,!1),()=>p.delete(e))}),[r,p,i]);return s&&h&&(_={..._}),(0,f.useMemo)(()=>{p.forEach((e,t)=>p.set(t,!1))},[r]),f.useEffect(()=>{!r&&!p.size&&i&&i()},[r]),e=(0,g.jsx)(v,{pop:c===`popLayout`,isPresent:r,anchorX:l,anchorY:u,root:d,children:e}),(0,g.jsx)(o.Provider,{value:_,children:e})};function y(){return new Map}var b=e=>e.key||``;function x(e){let t=[];return f.Children.forEach(e,e=>{(0,f.isValidElement)(e)&&t.push(e)}),t}var S=({children:e,custom:n,initial:r=!0,onExitComplete:a,presenceAffectsLayout:o=!0,mode:s=`sync`,propagate:u=!1,anchorX:d=`left`,anchorY:p=`top`,root:m})=>{let[h,_]=c(u),v=(0,f.useMemo)(()=>x(e),[e]),y=u&&!h?[]:v.map(b),S=(0,f.useRef)(!0),C=(0,f.useRef)(v),w=t(()=>new Map),T=(0,f.useRef)(new Set),[E,D]=(0,f.useState)(v),[O,k]=(0,f.useState)(v);l(()=>{S.current=!1,C.current=v;for(let e=0;e<O.length;e++){let t=b(O[e]);y.includes(t)?(w.delete(t),T.current.delete(t)):w.get(t)!==!0&&w.set(t,!1)}},[O,y.length,y.join(`-`)]);let A=[];if(v!==E){let e=[...v];for(let t=0;t<O.length;t++){let n=O[t],r=b(n);y.includes(r)||(e.splice(t,0,n),A.push(n))}return s===`wait`&&A.length&&(e=A),k(x(e)),D(v),null}let{forceRender:j}=(0,f.useContext)(i);return(0,g.jsx)(g.Fragment,{children:O.map(e=>{let t=b(e),i=u&&!h?!1:v===O||y.includes(t);return(0,g.jsx)(ee,{isPresent:i,initial:!S.current||r?void 0:!1,custom:n,presenceAffectsLayout:o,mode:s,root:m,onExitComplete:i?void 0:()=>{if(T.current.has(t))return;if(w.has(t))T.current.add(t),w.set(t,!0);else return;let e=!0;w.forEach(t=>{t||(e=!1)}),e&&(j?.(),k(C.current),u&&_?.(),a&&a())},anchorX:d,anchorY:p,children:e},t)})})},C=u(`circle-alert`,[[`circle`,{cx:`12`,cy:`12`,r:`10`,key:`1mglay`}],[`line`,{x1:`12`,x2:`12`,y1:`8`,y2:`12`,key:`1pkeuh`}],[`line`,{x1:`12`,x2:`12.01`,y1:`16`,y2:`16`,key:`4dfq90`}]]),w=u(`circle-check`,[[`circle`,{cx:`12`,cy:`12`,r:`10`,key:`1mglay`}],[`path`,{d:`m9 12 2 2 4-4`,key:`dzmm74`}]]),T=u(`info`,[[`circle`,{cx:`12`,cy:`12`,r:`10`,key:`1mglay`}],[`path`,{d:`M12 16v-4`,key:`1dtifu`}],[`path`,{d:`M12 8h.01`,key:`e9boi3`}]]),E=u(`x`,[[`path`,{d:`M18 6 6 18`,key:`1bl5f8`}],[`path`,{d:`m6 6 12 12`,key:`d8bk6v`}]]),D=u(`zap`,[[`path`,{d:`M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z`,key:`1xq2db`}]]),O=`/api/v1_7b82`,k=()=>window.Telegram?.WebApp,A=localStorage.getItem(`auth_token`),j=e=>{A=e,e?localStorage.setItem(`auth_token`,e):localStorage.removeItem(`auth_token`)},M=!1;async function N(e,t={},n=2){let r=`${O}${e}`,i={"Content-Type":`application/json`,...t.headers||{}};A&&(i.Authorization=`Bearer ${A}`);try{let a=await fetch(r,{...t,headers:i});if(a.status===401&&!M){M=!0;try{if(await te())return M=!1,N(e,t,n)}catch(e){console.error(`Auth Recovery Failed:`,e)}M=!1,j(null)}if(!a.ok){let e=await a.json().catch(()=>({}));throw Error(e.detail||`API error: ${a.status}`)}return await a.json()}catch(r){if(n>0&&(!t.method||t.method===`GET`))return console.warn(`Retrying [${e}]... (${n} left)`),N(e,t,n-1);throw console.error(`Fetch error [${e}]:`,r),r}}async function te(e=null){let t=k()?.initData,n=localStorage.getItem(`auth_token`),r={initData:t||null,token:n||null,avatar:e};try{let e=await fetch(`${O}/secure_init`,{method:`POST`,headers:{"Content-Type":`application/json`},body:JSON.stringify(r)});if(!e.ok)throw Error(`Init failed`);let t=await e.json();return t.token?(j(t.token),t.token):null}catch(e){return console.error(`Secure Init Error:`,e),null}}var ne={data:``},re=e=>{if(typeof window==`object`){let t=(e?e.querySelector(`#_goober`):window._goober)||Object.assign(document.createElement(`style`),{innerHTML:` `,id:`_goober`});return t.nonce=window.__nonce__,t.parentNode||(e||document.head).appendChild(t),t.firstChild}return e||ne},ie=/(?:([\u0080-\uFFFF\w-%@]+) *:? *([^{;]+?);|([^;}{]*?) *{)|(}\s*)/g,ae=/\/\*[^]*?\*\/|  +/g,P=/\n+/g,F=(e,t)=>{let n=``,r=``,i=``;for(let a in e){let o=e[a];a[0]==`@`?a[1]==`i`?n=a+` `+o+`;`:r+=a[1]==`f`?F(o,a):a+`{`+F(o,a[1]==`k`?``:t)+`}`:typeof o==`object`?r+=F(o,t?t.replace(/([^,])+/g,e=>a.replace(/([^,]*:\S+\([^)]*\))|([^,])+/g,t=>/&/.test(t)?t.replace(/&/g,e):e?e+` `+t:t)):a):o!=null&&(a=/^--/.test(a)?a:a.replace(/[A-Z]/g,`-$&`).toLowerCase(),i+=F.p?F.p(a,o):a+`:`+o+`;`)}return n+(t&&i?t+`{`+i+`}`:i)+r},I={},L=e=>{if(typeof e==`object`){let t=``;for(let n in e)t+=n+L(e[n]);return t}return e},oe=(e,t,n,r,i)=>{let a=L(e),o=I[a]||(I[a]=(e=>{let t=0,n=11;for(;t<e.length;)n=101*n+e.charCodeAt(t++)>>>0;return`go`+n})(a));if(!I[o]){let t=a===e?(e=>{let t,n,r=[{}];for(;t=ie.exec(e.replace(ae,``));)t[4]?r.shift():t[3]?(n=t[3].replace(P,` `).trim(),r.unshift(r[0][n]=r[0][n]||{})):r[0][t[1]]=t[2].replace(P,` `).trim();return r[0]})(e):e;I[o]=F(i?{[`@keyframes `+o]:t}:t,n?``:`.`+o)}let s=n&&I.g?I.g:null;return n&&(I.g=I[o]),((e,t,n,r)=>{r?t.data=t.data.replace(r,e):t.data.indexOf(e)===-1&&(t.data=n?e+t.data:t.data+e)})(I[o],t,r,s),o},se=(e,t,n)=>e.reduce((e,r,i)=>{let a=t[i];if(a&&a.call){let e=a(n),t=e&&e.props&&e.props.className||/^go/.test(e)&&e;a=t?`.`+t:e&&typeof e==`object`?e.props?``:F(e,``):!1===e?``:e}return e+r+(a??``)},``);function R(e){let t=this||{},n=e.call?e(t.p):e;return oe(n.unshift?n.raw?se(n,[].slice.call(arguments,1),t.p):n.reduce((e,n)=>Object.assign(e,n&&n.call?n(t.p):n),{}):n,re(t.target),t.g,t.o,t.k)}var z,B,V;R.bind({g:1});var H=R.bind({k:1});function ce(e,t,n,r){F.p=t,z=e,B=n,V=r}function U(e,t){let n=this||{};return function(){let r=arguments;function i(a,o){let s=Object.assign({},a),c=s.className||i.className;n.p=Object.assign({theme:B&&B()},s),n.o=/ *go\d+/.test(c),s.className=R.apply(n,r)+(c?` `+c:``),t&&(s.ref=o);let l=e;return e[0]&&(l=s.as||e,delete s.as),V&&l[0]&&V(s),z(l,s)}return t?t(i):i}}var le=e=>typeof e==`function`,W=(e,t)=>le(e)?e(t):e,ue=(()=>{let e=0;return()=>(++e).toString()})(),de=(()=>{let e;return()=>{if(e===void 0&&typeof window<`u`){let t=matchMedia(`(prefers-reduced-motion: reduce)`);e=!t||t.matches}return e}})(),fe=20,G=`default`,K=(e,t)=>{let{toastLimit:n}=e.settings;switch(t.type){case 0:return{...e,toasts:[t.toast,...e.toasts].slice(0,n)};case 1:return{...e,toasts:e.toasts.map(e=>e.id===t.toast.id?{...e,...t.toast}:e)};case 2:let{toast:r}=t;return K(e,{type:e.toasts.find(e=>e.id===r.id)?1:0,toast:r});case 3:let{toastId:i}=t;return{...e,toasts:e.toasts.map(e=>e.id===i||i===void 0?{...e,dismissed:!0,visible:!1}:e)};case 4:return t.toastId===void 0?{...e,toasts:[]}:{...e,toasts:e.toasts.filter(e=>e.id!==t.toastId)};case 5:return{...e,pausedAt:t.time};case 6:let a=t.time-(e.pausedAt||0);return{...e,pausedAt:void 0,toasts:e.toasts.map(e=>({...e,pauseDuration:e.pauseDuration+a}))}}},pe=[],me={toasts:[],pausedAt:void 0,settings:{toastLimit:fe}},q={},J=(e,t=G)=>{q[t]=K(q[t]||me,e),pe.forEach(([e,n])=>{e===t&&n(q[t])})},Y=e=>Object.keys(q).forEach(t=>J(e,t)),he=e=>Object.keys(q).find(t=>q[t].toasts.some(t=>t.id===e)),X=(e=G)=>t=>{J(t,e)},ge=(e,t=`blank`,n)=>({createdAt:Date.now(),visible:!0,dismissed:!1,type:t,ariaProps:{role:`status`,"aria-live":`polite`},message:e,pauseDuration:0,...n,id:n?.id||ue()}),Z=e=>(t,n)=>{let r=ge(t,e,n);return X(r.toasterId||he(r.id))({type:2,toast:r}),r.id},Q=(e,t)=>Z(`blank`)(e,t);Q.error=Z(`error`),Q.success=Z(`success`),Q.loading=Z(`loading`),Q.custom=Z(`custom`),Q.dismiss=(e,t)=>{let n={type:3,toastId:e};t?X(t)(n):Y(n)},Q.dismissAll=e=>Q.dismiss(void 0,e),Q.remove=(e,t)=>{let n={type:4,toastId:e};t?X(t)(n):Y(n)},Q.removeAll=e=>Q.remove(void 0,e),Q.promise=(e,t,n)=>{let r=Q.loading(t.loading,{...n,...n?.loading});return typeof e==`function`&&(e=e()),e.then(e=>{let i=t.success?W(t.success,e):void 0;return i?Q.success(i,{id:r,...n,...n?.success}):Q.dismiss(r),e}).catch(e=>{let i=t.error?W(t.error,e):void 0;i?Q.error(i,{id:r,...n,...n?.error}):Q.dismiss(r)}),e};var _e=H`
from {
  transform: scale(0) rotate(45deg);
	opacity: 0;
}
to {
 transform: scale(1) rotate(45deg);
  opacity: 1;
}`,ve=H`
from {
  transform: scale(0);
  opacity: 0;
}
to {
  transform: scale(1);
  opacity: 1;
}`,ye=H`
from {
  transform: scale(0) rotate(90deg);
	opacity: 0;
}
to {
  transform: scale(1) rotate(90deg);
	opacity: 1;
}`,be=U(`div`)`
  width: 20px;
  opacity: 0;
  height: 20px;
  border-radius: 10px;
  background: ${e=>e.primary||`#ff4b4b`};
  position: relative;
  transform: rotate(45deg);

  animation: ${_e} 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)
    forwards;
  animation-delay: 100ms;

  &:after,
  &:before {
    content: '';
    animation: ${ve} 0.15s ease-out forwards;
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
    animation: ${ye} 0.15s ease-out forwards;
    animation-delay: 180ms;
    transform: rotate(90deg);
  }
`,xe=H`
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
`,Se=U(`div`)`
  width: 12px;
  height: 12px;
  box-sizing: border-box;
  border: 2px solid;
  border-radius: 100%;
  border-color: ${e=>e.secondary||`#e0e0e0`};
  border-right-color: ${e=>e.primary||`#616161`};
  animation: ${xe} 1s linear infinite;
`,Ce=H`
from {
  transform: scale(0) rotate(45deg);
	opacity: 0;
}
to {
  transform: scale(1) rotate(45deg);
	opacity: 1;
}`,we=H`
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
}`,Te=U(`div`)`
  width: 20px;
  opacity: 0;
  height: 20px;
  border-radius: 10px;
  background: ${e=>e.primary||`#61d345`};
  position: relative;
  transform: rotate(45deg);

  animation: ${Ce} 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)
    forwards;
  animation-delay: 100ms;
  &:after {
    content: '';
    box-sizing: border-box;
    animation: ${we} 0.2s ease-out forwards;
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
`,Ee=U(`div`)`
  position: absolute;
`,De=U(`div`)`
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  min-width: 20px;
  min-height: 20px;
`,Oe=H`
from {
  transform: scale(0.6);
  opacity: 0.4;
}
to {
  transform: scale(1);
  opacity: 1;
}`,ke=U(`div`)`
  position: relative;
  transform: scale(0.6);
  opacity: 0.4;
  min-width: 20px;
  animation: ${Oe} 0.3s 0.12s cubic-bezier(0.175, 0.885, 0.32, 1.275)
    forwards;
`,Ae=({toast:e})=>{let{icon:t,type:n,iconTheme:r}=e;return t===void 0?n===`blank`?null:f.createElement(De,null,f.createElement(Se,{...r}),n!==`loading`&&f.createElement(Ee,null,n===`error`?f.createElement(be,{...r}):f.createElement(Te,{...r}))):typeof t==`string`?f.createElement(ke,null,t):t},je=e=>`
0% {transform: translate3d(0,${e*-200}%,0) scale(.6); opacity:.5;}
100% {transform: translate3d(0,0,0) scale(1); opacity:1;}
`,Me=e=>`
0% {transform: translate3d(0,0,-1px) scale(1); opacity:1;}
100% {transform: translate3d(0,${e*-150}%,-1px) scale(.6); opacity:0;}
`,Ne=`0%{opacity:0;} 100%{opacity:1;}`,Pe=`0%{opacity:1;} 100%{opacity:0;}`,Fe=U(`div`)`
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
`,Ie=U(`div`)`
  display: flex;
  justify-content: center;
  margin: 4px 10px;
  color: inherit;
  flex: 1 1 auto;
  white-space: pre-line;
`,Le=(e,t)=>{let n=e.includes(`top`)?1:-1,[r,i]=de()?[Ne,Pe]:[je(n),Me(n)];return{animation:t?`${H(r)} 0.35s cubic-bezier(.21,1.02,.73,1) forwards`:`${H(i)} 0.4s forwards cubic-bezier(.06,.71,.55,1)`}};f.memo(({toast:e,position:t,style:n,children:r})=>{let i=e.height?Le(e.position||t||`top-center`,e.visible):{opacity:0},a=f.createElement(Ae,{toast:e}),o=f.createElement(Ie,{...e.ariaProps},W(e.message,e));return f.createElement(Fe,{className:e.className,style:{...i,...n,...e.style}},typeof r==`function`?r({icon:a,message:o}):f.createElement(f.Fragment,null,a,o))}),ce(f.createElement),R`
  z-index: 9999;
  > * {
    pointer-events: auto;
  }
`;var Re=({current:e,total:t,color:n=`bg-brand-neon`,label:r})=>{let i=Math.min(100,Math.max(0,e/t*100));return(0,g.jsxs)(`div`,{className:`w-full space-y-1.5`,children:[r&&(0,g.jsxs)(`div`,{className:`flex justify-between items-end text-[10px] font-black text-slate-400 px-0.5 uppercase tracking-widest`,children:[(0,g.jsx)(`span`,{className:`opacity-70`,children:r}),(0,g.jsxs)(`span`,{className:`text-white/80 tabular-nums`,children:[e.toLocaleString(),` / `,t.toLocaleString()]})]}),(0,g.jsx)(`div`,{className:`h-2 w-full bg-slate-900/50 rounded-full overflow-hidden border border-white/10 p-[1px]`,children:(0,g.jsx)(a.div,{initial:{width:0},animate:{width:`${i}%`},transition:{duration:1.5,ease:[.34,1.56,.64,1]},className:`h-full ${n} rounded-full neon-shadow shadow-current relative`,children:(0,g.jsx)(`div`,{className:`absolute inset-0 bg-white/20 animate-pulse`})})})]})},$=({className:e})=>(0,g.jsx)(`div`,{className:`bg-white/5 overflow-hidden relative ${e}`,children:(0,g.jsx)(`div`,{className:`absolute inset-0 animate-shimmer`})}),ze=()=>(0,g.jsx)(`div`,{className:`rounded-2xl glass-panel border border-white/5 overflow-hidden`,children:(0,g.jsxs)(`div`,{className:`aspect-[3/4] p-3 flex flex-col justify-end space-y-2`,children:[(0,g.jsx)($,{className:`h-2 w-1/3 rounded`}),(0,g.jsx)($,{className:`h-3 w-2/3 rounded`})]})}),Be=({children:e,className:t=``})=>(0,g.jsx)(`div`,{className:`relative ${t}`,children:(0,g.jsx)(`div`,{className:`scroll-fade-mask overflow-x-auto no-scrollbar flex space-x-2 py-1`,children:e})}),Ve=(0,f.createContext)(null),He=({children:e})=>{let[t,n]=(0,f.useState)([]),r=(0,f.useCallback)((e,t=`info`)=>{let r=Math.random().toString(36).substr(2,9);n(n=>[...n,{id:r,message:e,type:t}]),setTimeout(()=>{n(e=>e.filter(e=>e.id!==r))},3e3)},[]);return(0,g.jsxs)(Ve.Provider,{value:{addToast:r},children:[e,(0,g.jsx)(`div`,{className:`fixed top-4 left-1/2 -translate-x-1/2 z-[300] w-full max-w-[280px] pointer-events-none flex flex-col items-center space-y-2`,children:(0,g.jsx)(S,{children:t.map(e=>(0,g.jsxs)(a.div,{initial:{y:-20,opacity:0,scale:.9},animate:{y:0,opacity:1,scale:1},exit:{y:-10,opacity:0,scale:.95},className:`glass-panel w-full px-4 py-3 rounded-2xl border border-white/10 shadow-2xl flex items-center space-x-3 pointer-events-auto`,children:[(0,g.jsx)(`div`,{className:e.type===`success`?`text-brand-neon`:e.type===`error`?`text-red-500`:`text-brand-accent`,children:e.type===`success`?(0,g.jsx)(w,{size:16}):(0,g.jsx)(C,{size:16})}),(0,g.jsx)(`span`,{className:`text-[10px] font-black uppercase tracking-widest text-slate-200 truncate pr-2`,children:e.message})]},e.id))})})]})},Ue=(e,t={},n=[])=>{let[r,i]=(0,f.useState)(t.initialData||null),[a,o]=(0,f.useState)(!t.manual),[s,c]=(0,f.useState)(null),l=(0,f.useRef)(t);((e,t)=>{let n=Object.keys(e),r=Object.keys(t);if(n.length!==r.length)return!1;for(let r of n)if(e[r]!==t[r])return!1;return!0})(l.current,t)||(l.current=t);let u=(0,f.useCallback)(async(t={})=>{o(!0),c(null);try{let n=await N(e,{...l.current,...t});return i(n),n}catch(e){throw c(e.message),e}finally{o(!1)}},[e]);return(0,f.useEffect)(()=>{l.current.manual||u()},n),{data:r,loading:a,error:s,execute:u,setData:i}},We=({character:e,onClose:t})=>((0,f.useEffect)(()=>{if(e){let e=document.querySelector(`.app-scroller`);return e&&(e.style.overflow=`hidden`),()=>{let e=document.querySelector(`.app-scroller`);e&&(e.style.overflow=`auto`)}}},[e]),e?(0,g.jsxs)(a.div,{initial:{opacity:0},animate:{opacity:1},exit:{opacity:0},className:`fixed inset-0 z-[100] flex items-end justify-center px-4 pb-12 pt-20`,children:[(0,g.jsx)(`div`,{className:`absolute inset-0 bg-brand-midnight/80 backdrop-blur-md`,onClick:t}),(0,g.jsxs)(a.div,{initial:{y:`100%`},animate:{y:0},exit:{y:`100%`},transition:{type:`spring`,damping:25,stiffness:200},className:`relative w-full max-w-sm glass-panel rounded-t-[2.5rem] overflow-hidden border-t-2 border-x border-white/20 flex flex-col pt-2 bg-gradient-to-b ${{Common:`from-slate-500/20 to-slate-900`,Rare:`from-blue-500/20 to-slate-900`,Epic:`from-purple-500/20 to-slate-900`,Legendary:`from-amber-500/20 to-slate-900`,Mythical:`from-red-500/20 to-slate-900`,Celestial:`from-cyan-400/20 to-slate-900`}[e.rarity]||`from-slate-800/10 to-slate-900`}`,children:[(0,g.jsx)(`div`,{className:`w-12 h-1.5 bg-white/20 rounded-full mx-auto mb-4`}),(0,g.jsx)(`button`,{onClick:t,className:`absolute top-3 right-3 p-1.5 rounded-full bg-white/5 text-white/50 hover:text-white transition-colors`,children:(0,g.jsx)(E,{size:18})}),(0,g.jsxs)(`div`,{className:`px-6 pb-8 overflow-y-auto`,children:[(0,g.jsx)(`div`,{className:`aspect-[4/5] rounded-3xl overflow-hidden border border-white/10 mb-6 shadow-[0_0_50px_rgba(0,0,0,0.5)] ${{Common:`shadow-slate-500/20`,Rare:`shadow-blue-500/40`,Epic:`shadow-purple-500/40`,Legendary:`shadow-amber-500/40`,Mythical:`shadow-red-500/40`,Celestial:`shadow-cyan-400/50 neon-shadow`}[e.rarity]}`,children:(0,g.jsx)(`img`,{src:e.img_url,alt:e.name,className:`w-full h-full object-cover`})}),(0,g.jsxs)(`div`,{className:`space-y-4 text-left`,children:[(0,g.jsxs)(`div`,{children:[(0,g.jsx)(`span`,{className:`px-2 py-1 rounded-md bg-white/10 text-[10px] font-black uppercase tracking-[0.2em] text-brand-neon border border-white/10 backdrop-blur-md`,children:e.rarity}),(0,g.jsx)(`h2`,{className:`text-2xl font-black mt-2 leading-tight uppercase tracking-tight text-white drop-shadow-sm line-clamp-2`,children:e.name}),(0,g.jsx)(`p`,{className:`text-slate-400 font-medium italic text-xs tracking-wide truncate`,children:e.anime})]}),(0,g.jsxs)(`div`,{className:`grid grid-cols-2 gap-3 pt-3 border-t border-white/5`,children:[(0,g.jsxs)(`div`,{className:`space-y-0.5`,children:[(0,g.jsx)(`p`,{className:`text-[9px] font-bold text-slate-500 uppercase tracking-widest`,children:`Global ID`}),(0,g.jsxs)(`p`,{className:`font-mono text-xs text-brand-neon`,children:[`#`,e.id]})]}),(0,g.jsxs)(`div`,{className:`space-y-0.5`,children:[(0,g.jsx)(`p`,{className:`text-[9px] font-bold text-slate-500 uppercase tracking-widest`,children:`Duplicates`}),(0,g.jsxs)(`p`,{className:`font-bold text-xs`,children:[`x`,e.count||1]})]})]}),e.count>1&&(0,g.jsxs)(`button`,{onClick:async()=>{try{if(!window.confirm(`Recycle 1 x ${e.name} for Zenith?`))return;await N(`/recycle`,{method:`POST`,body:JSON.stringify([e.id])}),Q.success(`Nexus Fusion Complete`),t(),window.dispatchEvent(new CustomEvent(`user-data-refresh`))}catch(e){Q.error(e.message||`Fusion failed`)}},className:`w-full py-2.5 rounded-lg bg-brand-accent/10 border border-brand-accent/20 text-brand-accent text-[10px] font-black uppercase tracking-widest hover:bg-brand-accent/20 transition-all flex items-center justify-center space-x-2`,children:[(0,g.jsx)(D,{size:12}),(0,g.jsx)(`span`,{children:`Recycle Duplicate`})]}),(0,g.jsxs)(`div`,{className:`flex items-center space-x-2 p-2.5 rounded-lg bg-white/5 border border-white/5 text-[9px] text-slate-400 font-medium italic`,children:[(0,g.jsx)(T,{size:12,className:`text-brand-neon shrink-0`}),(0,g.jsx)(`span`,{children:`Captured in group by this collector.`})]})]})]}),(0,g.jsx)(`div`,{className:`px-5 pb-5 pt-1`,children:(0,g.jsx)(`button`,{onClick:t,className:`w-full py-3 rounded-xl bg-white text-brand-midnight font-black uppercase tracking-widest text-[10px] hover:scale-[1.02] transition-transform active:scale-95`,children:`CLOSE DETAIL`})})]})]}):null),Ge=(0,f.memo)(({character:e,onClick:t})=>{let[n,r]=(0,f.useState)(e.img_url),[i,o]=(0,f.useState)(!1),s=`https://files.catbox.moe/2hsawz.jpg`,c={Common:`border-slate-500/30 shadow-slate-500/10`,Rare:`border-blue-500/30 shadow-blue-500/20`,Epic:`border-purple-500/30 shadow-purple-500/20`,Legendary:`border-amber-500/30 shadow-amber-500/20`,Mythical:`border-red-500/30 shadow-red-500/20`,Celestial:`border-cyan-400/40 shadow-cyan-400/30 neon-shadow`};return(0,g.jsx)(a.div,{whileHover:{scale:1.02},whileTap:{scale:.98},onClick:()=>{window.Telegram?.WebApp?.HapticFeedback?.impactOccurred(`medium`),t&&t()},className:`cursor-pointer overflow-hidden rounded-2xl glass-panel border transition-all ${(e=>c[e]||`border-slate-700/20 shadow-slate-700/5`)(e.rarity)}`,children:(0,g.jsxs)(`div`,{className:`aspect-[3/4] relative bg-slate-900/50`,children:[!i&&(0,g.jsx)(`div`,{className:`absolute inset-0 animate-pulse bg-gradient-to-r from-transparent via-white/10 to-transparent`}),(0,g.jsx)(`img`,{src:n||s,alt:e.name,className:cn(`w-full h-full object-cover transition-all duration-700`,i?`scale-100 blur-0 opacity-100`:`scale-110 blur-xl opacity-0`),onLoad:()=>o(!0),onError:()=>r(s),loading:`lazy`}),(0,g.jsx)(`div`,{className:`absolute inset-x-0 bottom-0 bg-gradient-to-t from-brand-midnight via-brand-midnight/60 to-transparent p-2.5 pt-8 text-left`,children:(0,g.jsxs)(`div`,{className:`flex justify-between items-end`,children:[(0,g.jsxs)(`div`,{className:`flex-1 truncate pr-1`,children:[(0,g.jsx)(`p`,{className:`text-[8px] font-black text-brand-neon uppercase tracking-widest mb-0.5 opacity-90 drop-shadow-[0_0_8px_rgba(0,255,255,0.4)]`,children:e.rarity}),(0,g.jsx)(`h3`,{className:`text-[11px] font-black truncate leading-none uppercase tracking-tight text-white/95`,children:e.name})]}),e.count>1&&(0,g.jsxs)(`span`,{className:`ml-1 bg-brand-neon text-brand-midnight text-[8px] font-black px-1.5 py-0.5 rounded-sm shadow-lg shadow-brand-neon/20 ring-1 ring-white/10`,children:[`x`,e.count]})]})})]})})});export{Be as a,Ue as c,te as d,D as f,Re as i,Q as l,S as m,ze as n,$ as o,w as p,We as r,He as s,Ge as t,N as u};