<script setup>
import {ref,computed,onMounted} from 'vue';
import {Search,Phone,Building2,LogIn,LogOut,Settings,Users,BookUser,ClipboardList,Plus,Pencil,Trash2,Save,X} from 'lucide-vue-next';
const token=ref(sessionStorage.getItem('directory_token')||'');const me=ref(null);const page=ref('directory');const contacts=ref([]),users=ref([]),audits=ref([]);const settings=ref({factory_name:'YOUR FACTORY NAME',subtitle:'Internal Telephone Directory',logo:'',theme:'light',font:'Roboto',palette:'slate',font_size:'jumbo',layout_size:'jumbo',intercom_prefix:'0442652',ui_text:{}});const filter=ref({name:'',unit:'',department:'',extension:''});const login=ref({email:'',password:''});const error=ref(''),success=ref('');const editId=ref(null);const contact=ref(blankContact());const account=ref(blankUser());const accountId=ref(null);

const defaultTexts = {
  "ui_001": "Directory",
  "ui_002": "Contacts",
  "ui_003": "Accounts",
  "ui_004": "Audit",
  "ui_005": "Settings",
  "ui_006": "Sign out",
  "ui_007": "Admin login",
  "ui_008": "COMPANY COMMUNICATIONS",
  "ui_009": "Telephone directory",
  "ui_010": "Find the right person, department or extension across your organisation.",
  "ui_011": "Find a contact",
  "ui_012": "Search by any combination of fields",
  "ui_013": "Name",
  "ui_014": "Unit",
  "ui_015": "All units",
  "ui_016": "Department",
  "ui_017": "All departments",
  "ui_018": "Extension",
  "ui_019": "Search",
  "ui_020": "Clear",
  "ui_021": "Contact results",
  "ui_022": "Name / Designation",
  "ui_023": "Unit",
  "ui_024": "Department",
  "ui_025": "Extension",
  "ui_026": "Phone",
  "ui_027": "No contacts found. Try changing your filters.",
  "ui_028": "SECURE ACCESS",
  "ui_029": "Administrator sign in",
  "ui_030": "Access is restricted to authorised personnel.",
  "ui_031": "Email address",
  "ui_032": "Password",
  "ui_033": "Sign in",
  "ui_034": "DIRECTORY MANAGEMENT",
  "ui_035": "Manage contacts",
  "ui_036": "Name",
  "ui_037": "Unit",
  "ui_038": "Department",
  "ui_039": "Extension",
  "ui_040": "Designation",
  "ui_041": "Phone",
  "ui_042": "Reset",
  "ui_043": "Contact records",
  "ui_044": "Name",
  "ui_045": "Unit",
  "ui_046": "Department",
  "ui_047": "Extension",
  "ui_048": "Actions",
  "ui_049": "ACCESS CONTROL",
  "ui_050": "Account management",
  "ui_051": "Assign accounts to the appropriate departments.",
  "ui_052": "Full name",
  "ui_053": "Email",
  "ui_054": "Password",
  "ui_055": "Role",
  "ui_056": "General user",
  "ui_057": "Department admin",
  "ui_058": "Super admin",
  "ui_059": "Department",
  "ui_060": "Status",
  "ui_061": "Active",
  "ui_062": "Disabled",
  "ui_063": "Save account",
  "ui_064": "Reset",
  "ui_065": "Registered accounts",
  "ui_066": "Name",
  "ui_067": "Email",
  "ui_068": "Role",
  "ui_069": "Department",
  "ui_070": "Actions",
  "ui_071": "PERSONALISATION",
  "ui_072": "Company branding",
  "ui_073": "Control the appearance of the public directory.",
  "ui_074": "Factory name",
  "ui_075": "Subtitle",
  "ui_076": "Logo URL (HTTPS) or upload",
  "ui_077": "Upload logo (max 250 KB)",
  "ui_078": "Font",
  "ui_079": "Inter",
  "ui_080": "Arial",
  "ui_081": "Georgia",
  "ui_082": "Theme",
  "ui_083": "Light",
  "ui_084": "Dark",
  "ui_085": "Colour palette",
  "ui_086": "Slate grey",
  "ui_087": "Charcoal",
  "ui_088": "Silver",
  "ui_089": "Save branding",
  "ui_090": "COMPLIANCE",
  "ui_091": "Contact audit history",
  "ui_092": "Latest 300 contact changes, including notification delivery status.",
  "ui_093": "UTC timestamp",
  "ui_094": "Admin",
  "ui_095": "Department",
  "ui_096": "Action",
  "ui_097": "Contact",
  "ui_098": "Email",
  "ui_099": "INTERNAL COMMUNICATIONS",
  "ui_100": "Corporate Telephone Directory · v1.0",
  "placeholder_101": "Employee name",
  "placeholder_102": "e.g. 2401",
  "placeholder_103": "https://...",
  "ui_104": "Edit contact",
  "ui_105": "Add new contact",
  "ui_106": "Update contact",
  "ui_107": "Create contact",
  "ui_108": "Edit account",
  "ui_109": "Create account",
  "ui_110": "(leave blank to keep)",
  "ui_111": "(minimum 10 characters)",
  "ui_112": "Department: ",
  "ui_113": "All departments"
};
const dialNumber = (extension) => { const prefix=String(settings.value.intercom_prefix || '0442652').replace(/\D/g,''); const ext=String(extension ?? '').replace(/\D/g,''); return ext ? prefix+ext : ''; };
const t = (key) => settings.value.ui_text?.[key] ?? defaultTexts[key] ?? key;
function resetText(){settings.value.ui_text={...defaultTexts}}

function blankContact(){return {name:'',unit:'',department:'',extension:'',designation:'',phone:''}}
function blankUser(){return {name:'',email:'',password:'',role:'user',department:'',active:true}}
async function api(path,opts={}){const r=await fetch('/api'+path,{...opts,headers:{'Content-Type':'application/json',...(token.value?{Authorization:'Bearer '+token.value}:{}),...(opts.headers||{})}});const d=await r.json();if(!r.ok)throw Error(d.error||'Request failed');return d}
async function execute(fn){error.value='';success.value='';try{await fn()}catch(e){error.value=e.message}}
async function load(){settings.value={...settings.value,...await api('/public/settings')};await search();if(token.value){try{me.value=await api('/me')}catch{logout()}}}
async function search(){const p=new URLSearchParams(Object.entries(filter.value).filter(([k,v])=>v));contacts.value=await api('/contacts?'+p)}
async function signIn(){await execute(async()=>{const r=await api('/login',{method:'POST',body:JSON.stringify(login.value)});token.value=r.token;sessionStorage.setItem('directory_token',r.token);me.value=r.user;page.value='directory';login.value.password='';success.value='Signed in successfully'})}
function logout(){token.value='';me.value=null;sessionStorage.removeItem('directory_token');page.value='directory'}
async function go(p){page.value=p;error.value='';success.value='';await execute(async()=>{if(p==='contacts'){contacts.value=await api('/manage/contacts');if(me.value?.role==='admin')contact.value.department=me.value.department;}if(p==='users'){users.value=await api('/users');if(me.value?.role==='admin')account.value.department=me.value.department;}if(p==='audit')audits.value=await api('/audit');if(p==='settings')settings.value={...settings.value,...await api('/settings')}})}
const units=computed(()=>[...new Set(contacts.value.map(x=>x.unit))].sort());const departments=computed(()=>[...new Set(contacts.value.map(x=>x.department))].sort());
function editContact(c){editId.value=c.id;contact.value={...c};window.scrollTo({top:0,behavior:'smooth'})}
async function saveContact(){await execute(async()=>{await api('/manage/contacts'+(editId.value?'/'+editId.value:''),{method:editId.value?'PUT':'POST',body:JSON.stringify(contact.value)});contact.value=blankContact();editId.value=null;contacts.value=await api('/manage/contacts');success.value='Contact saved'})}
async function removeContact(c){if(!confirm('Delete contact '+c.name+'?'))return;await execute(async()=>{await api('/manage/contacts/'+c.id,{method:'DELETE'});contacts.value=await api('/manage/contacts');success.value='Contact deleted'})}
function editUser(u){accountId.value=u.id;account.value={...u,password:''};window.scrollTo({top:0,behavior:'smooth'})}
async function saveUser(){await execute(async()=>{await api('/users'+(accountId.value?'/'+accountId.value:''),{method:accountId.value?'PUT':'POST',body:JSON.stringify(account.value)});accountId.value=null;account.value=blankUser();users.value=await api('/users');success.value='Account saved'})}
async function removeUser(u){if(!confirm('Delete account '+u.email+'?'))return;await execute(async()=>{await api('/users/'+u.id,{method:'DELETE'});users.value=await api('/users');success.value='Account deleted'})}
async function saveSettings(){await execute(async()=>{settings.value={...settings.value,...await api('/settings',{method:'PUT',body:JSON.stringify(settings.value)})};success.value='Settings and interface text saved'})}
function logoUpload(e){const f=e.target.files?.[0];if(!f)return;if(f.size>250000){error.value='Logo must be smaller than 250 KB';return}const r=new FileReader();r.onload=()=>settings.value.logo=r.result;r.readAsDataURL(f)}
onMounted(()=>execute(load));
</script>
<template>
<div class="shell" :class="[settings.theme==='dark'?'dark':'', 'font-size-'+(settings.font_size||'jumbo'), 'layout-size-'+(settings.layout_size||'jumbo')]" :style="{'--font':({'Roboto':'Roboto,Arial,sans-serif','Inter':'Inter,Arial,sans-serif','Arial':'Arial,sans-serif','Georgia':'Georgia,serif','Open Sans':'Open Sans,Arial,sans-serif','Lato':'Lato,Arial,sans-serif','Montserrat':'Montserrat,Arial,sans-serif','Poppins':'Poppins,Arial,sans-serif','Noto Sans':'Noto Sans,Arial,sans-serif','Verdana':'Verdana,sans-serif'}[settings.font]||'Roboto,Arial,sans-serif')}">
<header class="top"><div class="brand"><img v-if="settings.logo" :src="settings.logo" class="logo" alt="Factory logo"/><div v-else class="brand-icon"><Building2 :size="23"/></div><div><strong>{{settings.factory_name}}</strong><small>{{settings.subtitle}}</small></div></div><nav><button :class="{selected:page==='directory'}" @click="go('directory')"><Search :size="16"/> {{ t("ui_001") }}</button><template v-if="me&&me.role!=='user'"><button :class="{selected:page==='contacts'}" @click="go('contacts')"><BookUser :size="16"/> {{ t("ui_002") }}</button></template><template v-if="me?.role==='super_admin'"><button :class="{selected:page==='users'}" @click="go('users')"><Users :size="16"/> {{ t("ui_003") }}</button><button :class="{selected:page==='audit'}" @click="go('audit')"><ClipboardList :size="16"/> {{ t("ui_004") }}</button><button :class="{selected:page==='settings'}" @click="go('settings')"><Settings :size="16"/> {{ t("ui_005") }}</button></template><button v-if="me" @click="logout"><LogOut :size="16"/> {{ t("ui_006") }}</button><button v-else :class="{selected:page==='login'}" @click="go('login')"><LogIn :size="16"/> {{ t("ui_007") }}</button></nav></header>
<main><div v-if="error" class="notice bad">{{error}} <button @click="error=''">×</button></div><div v-if="success" class="notice good">{{success}} <button @click="success=''">×</button></div>
<section v-if="page==='directory'"><div class="hero"><div class="eyebrow">{{ t("ui_008") }}</div><h1>{{ t("ui_009") }}<span class="dot">.</span></h1><p>{{ t("ui_010") }}</p></div><div class="panel"><div class="section-title"><h2>{{ t("ui_011") }}</h2><span>{{ t("ui_012") }}</span></div><form class="filters" @submit.prevent="execute(search)"><label>{{ t("ui_013") }}<input v-model="filter.name" :placeholder="t('placeholder_101')"/></label><label>{{ t("ui_014") }}<select v-model="filter.unit"><option value="">{{ t("ui_015") }}</option><option v-for="v in units" :key="v">{{v}}</option></select></label><label>{{ t("ui_016") }}<select v-model="filter.department"><option value="">{{ t("ui_017") }}</option><option v-for="v in departments" :key="v">{{v}}</option></select></label><label>{{ t("ui_018") }}<input v-model="filter.extension" :placeholder="t('placeholder_102')"/></label><div class="filter-actions"><button class="primary" type="submit"><Search :size="17"/> {{ t("ui_019") }}</button><button type="button" @click="filter={name:'',unit:'',department:'',extension:''};execute(search)">{{ t("ui_020") }}</button></div></form></div><div class="panel results"><div class="section-title"><h2>{{ t("ui_021") }}</h2><span>{{contacts.length}} entries</span></div><div class="table-scroll"><table class="responsive-table"><thead><tr><th>{{ t("ui_022") }}</th><th>{{ t("ui_023") }}</th><th>{{ t("ui_024") }}</th><th>{{ t("ui_025") }}</th><th>{{ t("ui_026") }}</th></tr></thead><tbody><tr v-for="c in contacts" :key="c.id"><td :data-label="t('ui_022')"><b>{{c.name}}</b><small>{{c.designation||'—'}}</small></td><td :data-label="t('ui_023')">{{c.unit}}</td><td :data-label="t('ui_024')">{{c.department}}</td><td :data-label="t('ui_025')"><div class="extension-call"><span class="extension">{{c.extension}}</span><a v-if="dialNumber(c.extension)" class="call-intercom" :href="'tel:'+dialNumber(c.extension)" :aria-label="'Call ' + dialNumber(c.extension)" :title="'Call ' + dialNumber(c.extension)"><Phone :size="24"/><span>Call</span></a></div></td><td :data-label="t('ui_026')">{{c.phone||'—'}}</td></tr><tr v-if="!contacts.length"><td colspan="5" class="empty" data-empty="true">{{ t("ui_027") }}</td></tr></tbody></table></div></div></section>
<section v-else-if="page==='login'" class="login-panel panel"><div class="eyebrow">{{ t("ui_028") }}</div><h1>{{ t("ui_029") }}</h1><p>{{ t("ui_030") }}</p><form @submit.prevent="signIn"><label>{{ t("ui_031") }}<input v-model="login.email" type="email" required autocomplete="username"/></label><label>{{ t("ui_032") }}<input v-model="login.password" type="password" required autocomplete="current-password"/></label><button class="primary" type="submit">{{ t("ui_033") }}</button></form></section>
<section v-else-if="page==='contacts'&&me&&me.role!=='user'"><div class="page-heading"><div><div class="eyebrow">{{ t("ui_034") }}</div><h1>{{ t("ui_035") }}</h1><p>{{me.role==='admin'?t('ui_112')+me.department:t('ui_113')}}</p></div></div><div class="panel"><h2>{{editId?t('ui_104'):t('ui_105')}}</h2><form class="form-grid" @submit.prevent="saveContact"><label>{{ t("ui_036") }}<input v-model="contact.name" required/></label><label>{{ t("ui_037") }}<input v-model="contact.unit" required/></label><label>{{ t("ui_038") }}<input v-model="contact.department" :readonly="me.role==='admin'" required/></label><label>{{ t("ui_039") }}<input v-model="contact.extension" required/></label><label>{{ t("ui_040") }}<input v-model="contact.designation"/></label><label>{{ t("ui_041") }}<input v-model="contact.phone"/></label><div class="form-actions"><button class="primary"><Save :size="16"/> {{editId?t('ui_106'):t('ui_107')}}</button><button type="button" @click="editId=null;contact=blankContact()">{{ t("ui_042") }}</button></div></form></div><div class="panel"><h2>{{ t("ui_043") }}</h2><div class="table-scroll"><table class="responsive-table"><thead><tr><th>{{ t("ui_044") }}</th><th>{{ t("ui_045") }}</th><th>{{ t("ui_046") }}</th><th>{{ t("ui_047") }}</th><th>{{ t("ui_048") }}</th></tr></thead><tbody><tr v-for="c in contacts" :key="c.id"><td :data-label="t('ui_044')">{{c.name}}</td><td :data-label="t('ui_045')">{{c.unit}}</td><td :data-label="t('ui_046')">{{c.department}}</td><td :data-label="t('ui_047')">{{c.extension}}</td><td :data-label="t('ui_048')"><button @click="editContact(c)"><Pencil :size="15"/></button><button class="danger" @click="removeContact(c)"><Trash2 :size="15"/></button></td></tr></tbody></table></div></div></section>
<section v-else-if="page==='users'&&me?.role==='super_admin'"><div class="page-heading"><div class="eyebrow">{{ t("ui_049") }}</div><h1>{{ t("ui_050") }}</h1><p>{{ t("ui_051") }}</p></div><div class="panel"><h2>{{accountId?t('ui_108'):t('ui_109')}}</h2><form class="form-grid" @submit.prevent="saveUser"><label>{{ t("ui_052") }}<input v-model="account.name" required/></label><label>{{ t("ui_053") }}<input v-model="account.email" type="email" required/></label><label>{{ t("ui_054") }} <small>{{accountId?t('ui_110'):t('ui_111')}}</small><input v-model="account.password" type="password" :required="!accountId" minlength="10"/></label><label>{{ t("ui_055") }}<select v-model="account.role" :disabled="me.role==='admin'"><option value="user">{{ t("ui_056") }}</option><option value="admin">{{ t("ui_057") }}</option><option value="super_admin">{{ t("ui_058") }}</option></select></label><label v-if="account.role!=='super_admin'">{{ t("ui_059") }}<input v-model="account.department" required/></label><label v-if="accountId">{{ t("ui_060") }}<select v-model="account.active"><option :value="true">{{ t("ui_061") }}</option><option :value="false">{{ t("ui_062") }}</option></select></label><div class="form-actions"><button class="primary"><Save :size="16"/> {{ t("ui_063") }}</button><button type="button" @click="accountId=null;account=blankUser();account.department=me.role==='admin'?me.department:''">{{ t("ui_064") }}</button></div></form></div><div class="panel"><h2>{{ t("ui_065") }}</h2><div class="table-scroll"><table class="responsive-table"><thead><tr><th>{{ t("ui_066") }}</th><th>{{ t("ui_067") }}</th><th>{{ t("ui_068") }}</th><th>{{ t("ui_069") }}</th><th>{{ t("ui_070") }}</th></tr></thead><tbody><tr v-for="u in users" :key="u.id"><td :data-label="t('ui_066')">{{u.name}}</td><td :data-label="t('ui_067')">{{u.email}}</td><td :data-label="t('ui_068')">{{u.role}}</td><td :data-label="t('ui_069')">{{u.department||'—'}}</td><td :data-label="t('ui_070')"><button v-if="u.id!==me.id" @click="editUser(u)"><Pencil :size="15"/></button><button v-if="u.id!==me.id" class="danger" @click="removeUser(u)"><Trash2 :size="15"/></button></td></tr></tbody></table></div></div></section>
<section v-else-if="page==='settings'&&me?.role==='super_admin'"><div class="page-heading"><div class="eyebrow">{{ t("ui_071") }}</div><h1>{{ t("ui_072") }}</h1><p>{{ t("ui_073") }}</p></div><div class="panel"><form class="form-grid" @submit.prevent="saveSettings"><label>{{ t("ui_074") }}<input v-model="settings.factory_name"/></label><label>{{ t("ui_075") }}<input v-model="settings.subtitle"/></label><label>{{ t("ui_076") }}<input v-model="settings.logo" :placeholder="t('placeholder_103')"/></label><label>{{ t("ui_077") }}<input type="file" accept="image/*" @change="logoUpload"/></label><label>{{ t("ui_078") }}<select v-model="settings.font"><option value="Roboto">Roboto</option><option value="Inter">{{ t("ui_079") }}</option><option value="Arial">{{ t("ui_080") }}</option><option value="Georgia">{{ t("ui_081") }}</option><option value="Open Sans">Open Sans</option><option value="Lato">Lato</option><option value="Montserrat">Montserrat</option><option value="Poppins">Poppins</option><option value="Noto Sans">Noto Sans</option><option value="Verdana">Verdana</option></select></label><label>{{ t("ui_082") }}<select v-model="settings.theme"><option value="light">{{ t("ui_083") }}</option><option value="dark">{{ t("ui_084") }}</option></select></label><label>{{ t("ui_085") }}<select v-model="settings.palette"><option value="slate">{{ t("ui_086") }}</option><option value="charcoal">{{ t("ui_087") }}</option><option value="silver">{{ t("ui_088") }}</option></select></label><label>Font size<select v-model="settings.font_size"><option value="normal">Normal</option><option value="large">Large</option><option value="jumbo">Jumbo (default)</option><option value="extra_jumbo">Extra Jumbo</option><option value="giant">Giant</option></select></label><label>Layout size<select v-model="settings.layout_size"><option value="normal">Normal</option><option value="large">Large</option><option value="jumbo">Jumbo (default)</option><option value="extra_jumbo">Extra Jumbo</option><option value="giant">Giant</option></select></label><label>Intercom dialling prefix<input v-model="settings.intercom_prefix" type="tel" inputmode="numeric" pattern="[0-9]{1,15}" placeholder="0442652"/><small>Example: 0442652 + extension 6865 = 04426526865</small></label><div class="form-actions"><button class="primary"><Save :size="16"/> {{ t("ui_089") }}</button></div></form></div><div class="panel"><h2>Interface text customisation</h2><p>Changes apply to the directory, login, management pages, buttons, headings, table labels and footer for all users. Leave a field empty to hide its wording.</p><div class="form-grid"><label v-for="(defaultText,key) in defaultTexts" :key="key">{{defaultText}}<input v-model="settings.ui_text[key]" :placeholder="defaultText" /></label></div><div class="form-actions"><button class="primary" type="button" @click="saveSettings"><Save :size="16"/> Save all text changes</button><button type="button" @click="resetText">Restore default wording</button></div></div></section>
<section v-else-if="page==='audit'&&me?.role==='super_admin'"><div class="page-heading"><div class="eyebrow">{{ t("ui_090") }}</div><h1>{{ t("ui_091") }}</h1><p>{{ t("ui_092") }}</p></div><div class="panel table-scroll"><table class="responsive-table"><thead><tr><th>{{ t("ui_093") }}</th><th>{{ t("ui_094") }}</th><th>{{ t("ui_095") }}</th><th>{{ t("ui_096") }}</th><th>{{ t("ui_097") }}</th><th>{{ t("ui_098") }}</th></tr></thead><tbody><tr v-for="a in audits" :key="a.id"><td :data-label="t('ui_093')">{{a.time}}</td><td :data-label="t('ui_094')">{{a.actor_name}}<small>{{a.actor_email}}</small></td><td :data-label="t('ui_095')">{{a.department}}</td><td :data-label="t('ui_096')">{{a.action}}</td><td :data-label="t('ui_097')">{{a.after?.name||a.before?.name}}</td><td :data-label="t('ui_098')">{{a.email_status}}</td></tr></tbody></table></div></section>
</main><footer>{{ t("ui_099") }} <span>{{ t("ui_100") }}</span></footer></div>
</template>
