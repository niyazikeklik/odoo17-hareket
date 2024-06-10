/** @odoo-module **/

import public_kiosk_app from "@hr_attendance/public_kiosk/public_kiosk_app";
const kioskAttendanceApp = public_kiosk_app.kioskAttendanceApp;

import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { useService} from "@web/core/utils/hooks";
import { AttendanceRecognitionDialog } from "./attendance_recognition_dialog"
import { onWillStart, onMounted, useRef} from "@odoo/owl";
import { Deferred } from "@web/core/utils/concurrency";

import { loadBundle } from "@web/core/assets";

patch(kioskAttendanceApp.prototype, {
    setup() {
        super.setup();
        this.rpc = useService("rpc");
        this.dialog = useService("dialog");
        this.notificationService = useService("notification");

        // gelocation
        this.glocationContainerRef = useRef("glocation_container");
        this.glocationToggleRef = useRef("glocation_toggle");
        this.glocationViewRef = useRef("glocation_view");
        // geofence
        this.geofenceContainerRef = useRef("geofence_container");
        this.geofenceToggleRef = useRef("geofence_toggle");
        this.geofenceViewRef = useRef("geofence_view");
        // geoipaddress
        this.geoipaddressContainerRef = useRef("geoipaddress_container");
        this.geoipaddressToggleRef = useRef("geoipaddress_toggle");
        this.geoipaddressViewRef = useRef("geoipaddress_view");
        
        // session controls
        this.state.show_recognition = false;
        this.state.show_geolocation = false;
        this.state.show_geofence = false;
        this.state.show_ipaddress = false;

        //geolocation
        this.state.latitude = false;
        this.state.longitude = false;

        //geofence
        this.state.fence_ids = [];
        this.state.fence_is_inside = false;

        //ipaddress
        this.state.ipaddress = false;

        //recogniiton
        this.state.face_detected_employee = false;
        this.state.face_detected_photo = false;
        this.state.fece_is_main_init = false;

        //temp arrays
        this.labeledFaceDescriptors = [];

        onWillStart(async () => {   
            await this.loadResConfig();

            await loadBundle({
                cssLibs: [
                    '/hr_puantaj/static/src/lib/ol-6.12.0/ol.css',
                    '/hr_puantaj/static/src/lib/ol-ext/ol-ext.css',
                ],
                jsLibs: [
                    '/hr_puantaj/static/src/lib/ol-6.12.0/ol.js',
                    '/hr_puantaj/static/src/lib/ol-ext/ol-ext.js',
                ],
            });
        });

        onMounted(async () => {
            await this.loadControls();
        });
    },
    async loadControls(){
        if (window.location.protocol == 'https:') {
            
            this.geolocationDeferred = new Deferred();
            if (this.state.hr_attendance_geolocation_k) {                
                this.state.show_geolocation = true;
                this.state.latitude = false;
                this.state.longitude = false;                
                await this._getGeolocation();
            }else{
                this.geolocationDeferred.resolve();
            }

            this.geolocationMapDeferred = new Deferred();
            if (this.state.hr_attendance_geofence_k) {
                this.state.show_geofence = true;
                this.state.fence_ids = [];
                this.state.fence_is_inside = false;
                this.state.latitude = false;
                this.state.longitude = false;                                
                await this._getGeofenceMap();
            }else{
                this.geolocationMapDeferred.resolve();
            }

            this.recognitionDeferred = new Deferred();
            if (this.state.hr_attendance_face_recognition_k) {
                this.state.show_recognition = true;                
                await this._initRecognition();
            }else{
                this.recognitionDeferred.resolve();
            }

            this.geolocationAddressDeferred = new Deferred();
            if (this.state.hr_attendance_ip_k){
                this.state.show_ipaddress = true;
                this.state.ipaddress = false;                
                await this._getIpAddress();
            }else{
                this.geolocationAddressDeferred.resolve();
            }
        }else{
            this.state.show_geolocation = false;
            this.state.show_geofence = false;
            this.state.show_ipaddress = false;
            this.state.show_recognition = false;
        }
    },
    async loadResConfig(){
        const result = await this.rpc("/hr_attendance/attendance_res_config" ,{
            'token': this.props.token,
        });
        if (result){
            this.state.hr_attendance_geolocation_k = result.hr_attendance_geolocation_k ? result.hr_attendance_geolocation_k : false;
            this.state.hr_attendance_geofence_k = result.hr_attendance_geofence_k ? result.hr_attendance_geofence_k : false;
            this.state.hr_attendance_face_recognition_k = result.hr_attendance_face_recognition_k ? result.hr_attendance_face_recognition_k : false;
            this.state.hr_attendance_ip_k = result.hr_attendance_ip_k ? result.hr_attendance_ip_k : false;
        }
    },
    onToggleGeolocation(){
        var self = this;
        if (self.glocationToggleRef.el.classList.contains('fa-angle-double-down')) {
            self.glocationViewRef.el.classList.remove('d-none');
            self.glocationToggleRef.el.classList.toggle("fa-angle-double-down");
            self.glocationToggleRef.el.classList.toggle("fa-angle-double-up");
        }
        else {
            self.glocationViewRef.el.classList.add('d-none');
            self.glocationToggleRef.el.classList.toggle("fa-angle-double-down");
            self.glocationToggleRef.el.classList.toggle("fa-angle-double-up")
        }
    },
    async _getGeolocation () {
        var self = this;
        if (window.location.protocol == 'https:') {
            navigator.geolocation.getCurrentPosition(
                async ({coords: {latitude, longitude}}) => {
                    if (latitude && longitude){
                        self.state.latitude = latitude;
                        self.state.longitude = longitude;
                        self.geolocationDeferred.resolve();
                    }
                    else{
                        self.geolocationDeferred.reject();
                    }
                },
                async err => {
                    self.geolocationDeferred.reject();
                }
            );
        }else{
            self.geolocationDeferred.resolve();
        }
    },
    async onTogglegeofence(){
        var self = this;        
        if (self.geofenceToggleRef.el.classList.contains('fa-angle-double-down')) {
            self.geofenceViewRef.el.classList.remove('d-none');
            self.geofenceToggleRef.el.classList.toggle("fa-angle-double-down");
            self.geofenceToggleRef.el.classList.toggle("fa-angle-double-up");
            if (self.state.olmap){
                self.state.olmap.setTarget(self.geofenceViewRef.el);
                setTimeout(function () {
                    self.state.olmap.updateSize()
                }, 400);
            }else{
                await this._getGeofenceMap();
            }
        }
        else {
            self.geofenceViewRef.el.classList.add('d-none');
            self.geofenceToggleRef.el.classList.toggle("fa-angle-double-down");
            self.geofenceToggleRef.el.classList.toggle("fa-angle-double-up")
            self.state.olmap.setTarget(self.geofenceViewRef.el);
            if (self.state.olmap){
                self.state.olmap.setTarget(self.geofenceViewRef.el);
                setTimeout(function () {
                    self.state.olmap.updateSize()
                }, 400);
            }else{
                await this._getGeofenceMap();
            }
        }
    },
    _getGeofenceMap () {
        var self = this;
        if (window.location.protocol == 'https:') {
            navigator.geolocation.getCurrentPosition(
                async ({coords: {accuracy, latitude, longitude}}) => {
                    if (latitude && longitude){
                        self.state.latitude = latitude;
                        self.state.longitude = longitude;

                        if (!self.state.olmap) {
                            var vectorSource = new ol.source.Vector({});
                            self.state.olmap = await new ol.Map({
                                layers: [
                                    new ol.layer.Tile({
                                        source: new ol.source.OSM(),
                                    }),
                                    new ol.layer.Vector({
                                        source: vectorSource
                                    })
                                ],
        
                                loadTilesWhileInteracting: true,
                                view: new ol.View({
                                    center: [latitude, longitude],
                                    zoom: 2,
                                }),
                            });
                            self.state.olmap.setTarget(self.geofenceViewRef.el);
                            const Coords = [longitude, latitude];
                            const Accuracy = ol.geom.Polygon.circular(Coords, accuracy);
                            vectorSource.clear(true);
                            vectorSource.addFeatures([
                                new ol.Feature(Accuracy.transform('EPSG:4326', self.state.olmap.getView().getProjection())),
                                new ol.Feature(new ol.geom.Point(ol.proj.fromLonLat(Coords)))
                            ]);
                            self.state.olmap.getView().fit(vectorSource.getExtent(), { duration: 100, maxZoom: 6 });
                            setTimeout(function () {
                                self.state.olmap.updateSize()
                            }, 400);
        
                            self.geolocationMapDeferred.resolve();
                        }
                    }
                },
                async err => {
                    self.geolocationMapDeferred.reject();
                }
            );
        }else{
            self.geolocationMapDeferred.resolve();
        }        
    },
    onToggleGeoipaddress(){
        var self = this;

        if (self.geoipaddressToggleRef.el.classList.contains('fa-angle-double-down')) {
            self.geoipaddressViewRef.el.classList.remove('d-none');
            self.geoipaddressToggleRef.el.classList.toggle("fa-angle-double-down");
            self.geoipaddressToggleRef.el.classList.toggle("fa-angle-double-up");
        }
        else {
            self.geoipaddressViewRef.el.classList.add('d-none');
            self.geoipaddressToggleRef.el.classList.toggle("fa-angle-double-down");
            self.geoipaddressToggleRef.el.classList.toggle("fa-angle-double-up")
        }
    },
    async _getIpAddress(onNewIP) {
        var self = this;
        if (window.location.protocol == 'https:') {
            const response = await fetch("https://api.ipify.org?format=json");
            if (response.status == 200) {
                var text = await response.text();
                const data = JSON.parse(text);
                self.state.ipaddress = data.ip;
                self.geolocationAddressDeferred.resolve();
            }else{
                self.geolocationAddressDeferred.reject();
            }
        }else{
            self.geolocationAddressDeferred.resolve();
        }
    },
    async _initRecognition(){
        var self = this;
        if (window.location.protocol == 'https:') {
            if (!("faceapi" in window)) {
                self._loadFaceapi();
            } 
            else {
                await self._loadModels();
            }
        }else{
            self.recognitionDeferred.resolve();
        }
    },
    _loadFaceapi () {
        var self = this;
        if (!("faceapi" in window)) {
            (function (w, d, s, g, js, fjs) {
                g = w.faceapi || (w.faceapi = {});
                g.faceapi = { q: [], ready: function (cb) { this.q.push(cb); } };
                js = d.createElement(s); fjs = d.getElementsByTagName(s)[0];
                js.src = window.origin + '/hr_puantaj/static/src/lib/source/face-api.js';
                fjs.parentNode.insertBefore(js, fjs); js.onload = async function () {
                    console.log("apis loaded");
                    await self._loadModels();
                    self.def_face_recognition.resolve();
                };
            }(window, document, 'script'));
        }
    },
    async _loadModels() {
        var self = this;
        const promises = [];
        promises.push([
            faceapi.nets.tinyFaceDetector.loadFromUri('/hr_puantaj/static/src/lib/faceapi/weights'),
            faceapi.nets.faceLandmark68Net.loadFromUri('/hr_puantaj/static/src/lib/faceapi/weights'),
            faceapi.nets.faceLandmark68TinyNet.loadFromUri('/hr_puantaj/static/src/lib/faceapi/weights'),
            faceapi.nets.faceRecognitionNet.loadFromUri('/hr_puantaj/static/src/lib/faceapi/weights'),
            faceapi.nets.faceExpressionNet.loadFromUri('/hr_puantaj/static/src/lib/faceapi/weights'),
        ])
        return Promise.all(promises).then(() => {
            self.loadLabeledImages();            
            return Promise.resolve();
        });
    },
    async loadLabeledImages(){
        var self = this;
        return await this.rpc('/hr_puantaj/loadLabeledImages/').then(async function (data) {
            self.labeledFaceDescriptors = await Promise.all(
                data.map((data, i) => {  
                const descriptors = [];
                for (var i = 0; i < data.descriptors.length; i++) {                    
                    if (data.descriptors[i]){
                        descriptors.push(new Float32Array(new Uint8Array([...window.atob(data.descriptors[i])].map(d => d.charCodeAt(0))).buffer));
                    }
                }
                return new faceapi.LabeledFaceDescriptors(data.label.toString(), descriptors);
            }));
            if (self.labeledFaceDescriptors.length > 0){
                self.recognitionDeferred.resolve();
            }
        });
    },
    async _validate_Geofence (employeeId) {
        var self = this;
        this.state.fence_ids = [];
        this.state.fence_is_inside = false;
        const def = new Deferred();
        if (window.location.protocol == 'https:') {
            const records = await this.rpc('/hr_attendance/get_geofences/', {
                'token': self.props.token,
                'employee_id': parseInt(employeeId),
            })
            
            if (records.length > 0){
                var geofence_data = records.length && records;

                if (!geofence_data.length) {
                    def.reject();
                }
                navigator.geolocation.getCurrentPosition(
                    async ({coords: {latitude, longitude}}) => {
                        if (latitude && longitude){
                            if (self.state.olmap) {
                                for (let i = 0; i < geofence_data.length; i++) {
                                    var path = geofence_data[i].overlay_paths;
                                    var value = JSON.parse(path);
                                    if (Object.keys(value).length > 0) {
                                        let coords = ol.proj.fromLonLat([longitude, latitude]);
                                        var features = new ol.format.GeoJSON().readFeatures(value);
                                        var geometry = features[0].getGeometry();
                                        self.state.fence_is_inside = geometry.intersectsCoordinate(coords);
                                        
                                        if (self.state.fence_is_inside === true) {
                                            self.state.fence_ids.push(parseInt(geofence_data[i].id));
                                        }
                                    }
                                }
        
                                if ( self.state.fence_ids.length > 0) {
                                    def.resolve();
                                } 
                                else {
                                    def.reject();
                                }
                            }
                        }
                    },
                    async err => {
                        def.reject();
                    }
                );
            }
            else{
                self.state.fence_is_inside = false;
                self.state.fence_ids = [];
                def.resolve();
            }
        }else{
            def.resolve();
        }
        return def;
    },
    onClickRecongintion(){
        var self = this;
        console.log("test recog1");
        if (self.state.show_recognition) {
            self.state.face_detected_employee = false;
            self.state.face_detected_photo = false;
            self.state.fece_is_main_init = true;
            console.log("test recog2");
            self.dialog.add(AttendanceRecognitionDialog, {
                faceapi: faceapi,
                labeledFaceDescriptors : this.labeledFaceDescriptors,
                updateRecognitionAttendance: (rdata) => this.updateRecognitionAttendance(rdata),
            });
        }
    },
    async updateRecognitionAttendance( rdata ) {
        var self = this;

        var employeeId = parseInt(rdata.employee_id);
        
        self.state.face_detected_employee = rdata.employee_id;
        self.state.face_detected_photo = rdata.image;

        if (!employeeId){
            return self.notificationService.add(
                _t("Failed: Please try again. Employee not found."), 
                { type: "danger" }
            );
        }

        const employee = await this.rpc('attendance_employee_data',{
            'token': this.props.token,
            'employee_id': employeeId,
        })

        if (employee && employee.employee_name){
            if (employee.use_pin){
                self.employeeData = employee;
                self.switchDisplay('pin');
            }
            else{
                await this.onManualSelection(employeeId, false)
            }
        }
    },
    async onManualSelection(employeeId, enteredPin){
        var self = this;
        if (this.state.show_recognition || this.state.show_geolocation || this.state.show_geofence || this.state.show_ipaddress) {
            
            var c_latitude = false;
            var c_longitude = false;
            var c_fence_ids = [];
            var c_fence_is_inside = false;
            var c_photo = false;
            var c_employee_id = false;
            var c_ipaddress = false;

            const def_geolocation = new Deferred();                
            if (self.state.show_geolocation) {
                c_latitude = self.state.latitude || '';
                c_longitude = self.state.longitude || '';
                if (c_latitude && c_longitude){
                    def_geolocation.resolve();
                }else{
                    def_geolocation.reject();
                    self.notificationService.add(_t("Location not loaded, Please try again."), {
                        type: "danger",
                    });
                }
            }else{
                def_geolocation.resolve();
            }

            const def_geofence = new Deferred();
            if (self.state.show_geofence) {
                var fence = await self._validate_Geofence(employeeId);
                
                c_fence_ids = Object.values(self.state.fence_ids);
                c_fence_is_inside = self.state.fence_is_inside;

                if (c_fence_ids.length > 0 && c_fence_is_inside){
                    def_geofence.resolve();
                }else{
                    def_geofence.reject();
                    self.notificationService.add(_t("You haven't entered any of the geofence zones."), {
                        type: "danger",
                    });                   
                }
            }else{
                def_geofence.resolve();
            }
            
            const def_recognigtion = new Deferred();
            if (self.state.show_recognition && self.state.fece_is_main_init){
                c_photo = self.state.face_detected_photo;
                c_employee_id = self.state.face_detected_employee;
                if (c_photo && c_employee_id){
                    def_recognigtion.resolve();
                }
                else{                    
                    def_recognigtion.reject();                    
                    self.notificationService.add(
                        _t("Failed Face Detection: Please try again. Something went wrong."), 
                        { type: "danger" }
                    );
                }               
            }else{
                def_recognigtion.resolve();
            }

            const def_ipaddress = new Deferred();
            if (self.state.show_ipaddress) {
                c_ipaddress = self.state.ipaddress || '-';
                if (c_ipaddress){
                    def_ipaddress.resolve();
                }else{      
                    def_ipaddress.resolve();
                    return self.notificationService.add(_t("IP Adderess not loaded, Please try again."), {
                        type: "danger",
                    });                    
                }
            }else{
                def_ipaddress.resolve();
            }
            
            // Reverting Recogition States
            self.state.face_detected_photo = false;
            self.state.face_detected_employee= false;
            self.state.fece_is_main_init = false;

            Promise.all([def_geolocation , def_geofence , def_recognigtion, def_ipaddress ]).then(async function () {  
                const result = await self.rpc('manual_selection',
                {
                    'token': self.props.token,
                    'employee_id': employeeId,
                    'pin_code': enteredPin,
                })
                if (result && result.attendance) {                     
                    if (result.attendance.id && result.attendance_state == "checked_in"){
                        await self.rpc('update_checkin_controls',{
                            'token': self.props.token,
                            'attendance_id':parseInt(result.attendance.id),
                            'check_in_latitude': c_latitude,
                            'check_in_longitude': c_longitude,
                            'check_in_geofence_ids': c_fence_ids,
                            'check_in_photo': c_photo,
                            'check_in_ipaddress': c_ipaddress,
                        })
                    }
                    else if(result.attendance.id && result.attendance_state == "checked_out"){
                        await self.rpc('update_checkout_controls',{
                            'token': self.props.token,
                            'attendance_id':parseInt(result.attendance.id),
                            'check_out_latitude': c_latitude,
                            'check_out_longitude': c_longitude,
                            'check_out_geofence_ids': c_fence_ids,
                            'check_out_photo': c_photo,
                            'check_out_ipaddress': c_ipaddress,
                        })
                    }
                    self.employeeData = result
                    self.switchDisplay('greet')
                }
                else{
                    if (enteredPin){
                        self.displayNotification(_t("Wrong Pin"))
                    }
                }
            }).catch((err) => {
                console.log(err)
            });
        }else{
            const result = await this.rpc('manual_selection',
            {
                'token': this.props.token,
                'employee_id': employeeId,
                'pin_code': enteredPin
            })
            if (result && result.attendance) {
                this.employeeData = result
                this.switchDisplay('greet')
            }else{
                if (enteredPin){
                    this.displayNotification(_t("Wrong Pin"))
                }
            }
        } 
    },
});

