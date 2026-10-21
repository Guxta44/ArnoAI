/* Interações do redesign Arno AI: progresso, cursor e cards responsivos */
(function(){
 const reduced=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
 const fine=window.matchMedia('(hover: hover) and (pointer: fine)').matches;
 const progress=document.createElement('div');progress.className='arno-scroll-progress';progress.setAttribute('aria-hidden','true');document.body.appendChild(progress);
 let ticking=false;
 function update(){const max=document.documentElement.scrollHeight-window.innerHeight;progress.style.transform='scaleX('+ (max>0?Math.min(1,Math.max(0,window.scrollY/max)):0)+')';ticking=false}
 window.addEventListener('scroll',()=>{if(!ticking){requestAnimationFrame(update);ticking=true}},{passive:true});update();
 if(reduced)return;
 if(fine){
  const dot=document.createElement('div'),ring=document.createElement('div');dot.className='arno-cursor';ring.className='arno-cursor-ring';dot.setAttribute('aria-hidden','true');ring.setAttribute('aria-hidden','true');document.body.append(dot,ring);
  let x=innerWidth/2,y=innerHeight/2,rx=x,ry=y;
  document.addEventListener('mousemove',e=>{x=e.clientX;y=e.clientY;dot.style.left=x+'px';dot.style.top=y+'px';document.body.style.setProperty('--pointer-x',x+'px');document.body.style.setProperty('--pointer-y',y+'px');dot.classList.add('is-visible');ring.classList.add('is-visible')},{passive:true});
  function follow(){rx+=(x-rx)*.17;ry+=(y-ry)*.17;ring.style.left=rx+'px';ring.style.top=ry+'px';requestAnimationFrame(follow)}follow();
  document.addEventListener('mouseover',e=>ring.classList.toggle('is-hovering',!!e.target.closest('a,button,.feature-card,.workout-card,.step,.print-item')));
  document.addEventListener('mouseleave',()=>{dot.classList.remove('is-visible');ring.classList.remove('is-visible')});
  document.querySelectorAll('.feature-card,.workout-card,.print-item').forEach(card=>{
   card.addEventListener('mousemove',e=>{const r=card.getBoundingClientRect(),px=(e.clientX-r.left)/r.width,py=(e.clientY-r.top)/r.height;card.style.setProperty('--mx',(e.clientX-r.left)+'px');card.style.setProperty('--my',(e.clientY-r.top)+'px');card.style.transform='perspective(900px) rotateX('+((.5-py)*2.5)+'deg) rotateY('+((px-.5)*3.5)+'deg) translateY(-4px)'});
   card.addEventListener('mouseleave',()=>card.style.transform='');
  });
 }
})();
