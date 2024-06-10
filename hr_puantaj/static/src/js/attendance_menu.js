/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { ActivityMenu } from "@hr_attendance/components/attendance_menu/attendance_menu";

import { useService } from "@web/core/utils/hooks";
import { onWillStart, useRef } from "@odoo/owl";
import { session } from "@web/session";
import { loadBundle } from "@web/core/assets";
import { Deferred } from "@web/core/utils/concurrency";

import { AttendanceRecognitionDialog } from "./attendance_recognition_dialog"
import { AttendanceWebcamDialog } from "./attendance_webcam_dialog"


patch(ActivityMenu.prototype, {
    setup() {
        super.setup();
        this.rpc = useService("rpc");
        this.orm = useService('orm');
        this.dialog = useService("dialog");
        this.notificationService = useService('notification');
        
        //work type
        this.workTypeContainerRef = useRef("work_type_container");
        this.workTypeToggleRef = useRef("work_type_toggle");
        this.workTypeViewRef = useRef("work_type_view");
        this.workTypeInputRef = useRef("work_types_input");

        //project
        this.projectContainerRef = useRef("project_container");
        this.projectToggleRef = useRef("project_toggle");
        this.projectViewRef = useRef("project_view");
        this.projectInputRef = useRef("projects_input");

        //work
        this.workContainerRef = useRef("work_container");
        this.workToggleRef = useRef("work_toggle");
        this.workViewRef = useRef("work_view");
        this.workInputRef = useRef("work_input");

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
        this.show_geolocation = false;
        this.show_geofence = false;
        this.show_ipaddress = false;
        this.show_recognition = false;
        this.show_photo = false;
        this.show_work_type = false;

        // gelocation
        this.state.latitude = false;
        this.state.longitude = false;
        // geofence
        this.state.olmap = false;
        this.state.fence_is_inside = false;
        this.state.fence_ids = [];
        //ipaddress
        this.state.ipaddress = false;
        this.state.work_desription = "";

        //temp arrays
        this.work_types = [];
        this.projects = [];
        this.labeledFaceDescriptors = [];

        onWillStart(async () => {
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
        this.loadControls();
                this.actionService = useService("action");

                  this.actionService.doAction("hr_puantaj.action_work_entry_wizard");
    },
    async loadControls(){
        if (window.location.protocol == 'https:') {

            this.geolocationDeferred = new Deferred();
            if (session.hr_attendance_geolocation) {
                this.show_geolocation = true;
                this.state.latitude = false;
                this.state.longitude = false;
                await this._getGeolocation();
            }else{
                this.geolocationDeferred.resolve();
            }

            this.geolocationMapDeferred = new Deferred();
            if (session.hr_attendance_geofence) {
                this.show_geofence = true;
                this.state.fence_ids = [];
                this.state.fence_is_inside = false;
                this.state.latitude = false;
                this.state.longitude = false;                
                await this._getGeofenceMap();
            }else{
                this.geolocationMapDeferred.resolve();
            }

            this.geolocationAddressDeferred = new Deferred();
            if (session.hr_attendance_ip) {
                this.show_ipaddress = true;
                this.state.ipaddress = false;                
                await this._getIpAddress();
            }else{
                this.geolocationAddressDeferred.resolve();
            }

            this.recognitionDeferred = new Deferred();
            if (session.hr_attendance_face_recognition){
                this.show_recognition = true;
                this.recognitionDeferred = new Deferred();
                await this._initRecognition();
            }else{
                this.recognitionDeferred.resolve();
            }

            if (session.hr_attendance_photo){
                this.show_photo = true;
            }

        }else{
            this.show_geolocation = false;
            this.show_geofence = false;
            this.show_ipaddress = false;
            this.show_recognition = false;
            this.show_photo = false;
        }
        if (session.hr_attendance_work_type){
            this.show_work_type = true;
            await this._getWorkTypes();
            await this._getProjects();
            await this._getCheckInData();
        }else{
            this.show_work_type = false;
        }
    },
    onToggleGeolocation(){
        var self = this;
        if ($(self.glocationToggleRef.el).hasClass('fa-angle-double-down')) {
            $(self.glocationViewRef.el).removeClass('d-none');
            $(self.glocationToggleRef.el).toggleClass("fa-angle-double-down fa-angle-double-up");
        }
        else {
            $(self.glocationViewRef.el).addClass('d-none');
            $(self.glocationToggleRef.el).toggleClass("fa-angle-double-up fa-angle-double-down");
        }
    },
    async _getGeolocation () {
        var self = this;
        if (window.location.protocol == 'https:') {
            navigator.geolocation.getCurrentPosition(
                async ({coords: {latitude, longitude}}) => {
                    self.state.latitude = latitude;
                    self.state.longitude = longitude;
                    self.geolocationDeferred.resolve();
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
        if ($(self.geofenceToggleRef.el).hasClass('fa-angle-double-down')) {
            $(self.geofenceViewRef.el).removeClass('d-none');
            $(self.geofenceToggleRef.el).toggleClass("fa-angle-double-down fa-angle-double-up");
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
            $(self.geofenceViewRef.el).addClass('d-none');
            $(self.geofenceToggleRef.el).toggleClass("fa-angle-double-up fa-angle-double-down");
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
                            var olmap_div = self.geofenceViewRef.el;
                            
                            $(olmap_div).css({
                                width: '350px !important',
                                height: '200px !important'
                            });
        
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
        if ($(self.geoipaddressToggleRef.el).hasClass('fa-angle-double-down')) {
            $(self.geoipaddressViewRef.el).removeClass('d-none');
            $(self.geoipaddressToggleRef.el).toggleClass("fa-angle-double-down fa-angle-double-up");
        }
        else {
            $(self.geoipaddressViewRef.el).addClass('d-none');
            $(self.geoipaddressToggleRef.el).toggleClass("fa-angle-double-up fa-angle-double-down");
        }
    },
    async _getIpAddress(onNewIP) {
        var self = this;
        if (window.location.protocol == 'https:') {
            await $.getJSON("https://api.ipify.org?format=json", function (data) {
                if (data.ip) {
                    self.state.ipaddress = data.ip;
                    self.geolocationAddressDeferred.resolve();
                }else{
                    self.geolocationAddressDeferred.reject();
                }
            });
        }else{
            self.geolocationAddressDeferred.resolve();
        }
    },
    onToggleWorkType(){
        var self = this;
        if ($(self.workTypeToggleRef.el).hasClass('fa-angle-double-down')) {
            $(self.workTypeViewRef.el).removeClass('d-none');
            $(self.workTypeToggleRef.el).toggleClass("fa-angle-double-down fa-angle-double-up");
        }
        else {
            $(self.workTypeViewRef.el).addClass('d-none');
            $(self.workTypeToggleRef.el).toggleClass("fa-angle-double-up fa-angle-double-down");
        }
    },
    onToggleProject(){
        var self = this;
        if ($(self.projectToggleRef.el).hasClass('fa-angle-double-down')) {
            $(self.projectViewRef.el).removeClass('d-none');
            $(self.projectToggleRef.el).toggleClass("fa-angle-double-down fa-angle-double-up");
        }
        else {
            $(self.projectViewRef.el).addClass('d-none');
            $(self.projectToggleRef.el).toggleClass("fa-angle-double-up fa-angle-double-down");
        }
    },
    onToggleWork(){
        var self = this;
        if ($(self.workToggleRef.el).hasClass('fa-angle-double-down')) {
            $(self.workViewRef.el).removeClass('d-none');
            $(self.workToggleRef.el).toggleClass("fa-angle-double-down fa-angle-double-up");
        }
        else {
            $(self.workViewRef.el).addClass('d-none');
            $(self.workToggleRef.el).toggleClass("fa-angle-double-up fa-angle-double-down");
        }
    },
    async _getWorkTypes(){
        var self = this;
        await self.rpc("/web/dataset/call_kw/hr.work.entry.type/search_read", {
            model: "hr.work.entry.type",
            method: "search_read",
            args: [[], ['id', 'name', 'code']],
            kwargs: {},
        }).then(function(work_types){
            self.work_types = work_types;
        });
    },
    async _getProjects(){
        var self = this;
        await self.rpc("/web/dataset/call_kw/harkt.proje/search_read", {
            model: "harkt.proje",
            method: "search_read",
            args: [[], ['id', 'name', 'code']],
            kwargs: {},
        }).then(function(projects){
            self.projects = projects;
        });
    },
    async _getCheckInData() {
        var self = this;
        if(!self.check_in_work_type_id)
        {
            if (this.employee.attendance != null && this.state.checkedIn) {
                await self.rpc("/web/dataset/call_kw/hr.attendance/search_read", {
                    model: "hr.attendance",
                    method: "search_read",
                    args: [[["id", "=", this.employee.attendance.id]], ['check_in_work_type_id', 'check_in_work', 'check_in_project_id']],
                    kwargs: {},
                    limit: 1
                }).then(function (check_in_data) {
                    self.check_in_work_type_id = check_in_data[0].check_in_work_type_id[0];
                    self.check_in_work = check_in_data[0].check_in_work;
                    self.check_in_project_id = check_in_data[0].check_in_project_id[0]
                });

            } else {

                try{
                    self.check_in_work_type_id = 0;
                    self.check_in_work = "";
                    self.check_in_project_id = 0;
                  }
                  catch(err)
                  {

                  }
            }
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

    async _validate_Geofence () {
        var self = this;
        const def = new Deferred();
        if (window.location.protocol == 'https:') {
            const company_id = session.user_companies.allowed_companies[0] || session.user_companies.current_company || false;
            const records = await self.orm.call('hr.attendance.geofence', "search_read", [[['company_id', '=', company_id]], ['id', 'name', 'overlay_paths']], {});

            if (records.length > 0){
                var geofence_data = records.length && records;
                if (!geofence_data.length) {
                    def.reject();
                }
                def.resolve();
                navigator.geolocation.getCurrentPosition(
                    async ({coords: {latitude, longitude}}) => {
                        if (latitude && longitude){
                            if (self.state.olmap) {
                                self.state.fence_ids = [];
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
    async signInOut() {
        var self = this;
        this.reload_menu =1;

        if (self.show_work_type && $(self.workInputRef.el).val() == "" || $(self.workTypeInputRef.el).val() == "") {
            console.log("Mesai tipini ve Yapılan işi girmelisiniz");
            //this.widget.displayNotification({ message: 'Mesai tipini ve Yapılan işi girmelisiniz', type: 'error' });
            this.env.services['action'].doAction({
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Zorunlu Değerler',
                    'message': "Mesai tipini ve Yapılan işi alanlarının doldurulması zorunludur",
                    'type': 'danger',
                    'sticky': false,
                }
            });

            //alert("Mesai tipini ve Yapılan işi girmelisiniz");
        }
        else if (self.show_geolocation || self.show_geofence  || self.show_ipaddress ||
            self.show_recognition || self.show_photo || self.show_work_type) {

                var c_latitude = false;
                var c_longitude = false;
                var c_fence_ids = [];
                var c_fence_is_inside = false;
                var c_ipaddress = false;
                var c_photo = false;
                var c_work_type = false;
                //mimol 22042024 start
                var c_project = false;
                var c_work = false;
                var reload_menu = 0;

                const def_project = new Deferred();
                console.log("her we go");
                console.log(window.location);
                //await this._getCheckInData();

                if (self.show_work_type){
                    c_project = $(self.projectInputRef.el).val() || '-';
                    if (c_project) {
                        def_project.resolve();
                    }else{
                        def_project.reject();
                    }
                }
                else
                {
                    def_project.resolve();
                }
                console.log("c_project")
                console.log(c_project)

                const def_work = new Deferred();
                if (self.show_work_type)
                {
                    c_work = $(self.workInputRef.el).val();
                    if (c_work) {
                        def_work.resolve();
                    }else{
                        def_work.reject();
                    }
                }else{
                    def_work.resolve();
                }

                const def_work_type = new Deferred();
                if (self.show_work_type){
                    c_work_type = $(self.workTypeInputRef.el).val() || '-';
                    if (c_work_type) {
                        def_work_type.resolve();
                    }else{
                        def_work_type.reject();
                    }
                }else{
                    def_work_type.resolve();
                }
                console.log("c_work_type")
                console.log(c_work_type)

                console.log(self.workTypeInputRef.el);
                try {
                    self.check_in_work_type_id = c_work_type;
                    self.check_in_project_id = c_project;
                    self.check_in_work = c_work;
                }
                catch(exc)
                {

                }
                //mimol 22042024 finish

                const def_geolocation = new Deferred();
                if (self.show_geolocation) {
                    c_latitude = self.state.latitude || '';
                    c_longitude = self.state.longitude || '';
                    def_geolocation.resolve();
                }else{
                    def_geolocation.resolve();
                }


                const def_geofence = new Deferred();
                if (self.show_geofence) {
                    var fence = await self._validate_Geofence();
                    await new Promise(r => setTimeout(r, 1000));
                    c_fence_ids = Object.values(self.state.fence_ids);
                    c_fence_is_inside = self.state.fence_is_inside;
                    def_geofence.resolve();
                    if (c_fence_ids.length >0  && c_fence_is_inside){
                        def_geofence.resolve();

                    }else{
                        def_geofence.reject();
                        self.notificationService.add(_t("Herhangi bir proje lokasyonu içinde görünmüyorsunuz"), {
                            type: "danger",
                        });
                    }
                }else{
                    def_geofence.resolve();
                }

                const def_ipaddress = new Deferred();
                if (self.show_ipaddress) {
                    c_ipaddress = self.state.ipaddress || '-';
                    if (c_ipaddress){
                        def_ipaddress.resolve();
                    }else{
                        def_ipaddress.reject();
                        self.notificationService.add(_t("IP Adderess not loaded, Please try again."), {
                            type: "danger",
                        });
                    }
                }else{
                    def_ipaddress.resolve();
                }

                const def_recognigtion = new Deferred();
                if (self.show_recognition){
                    if (self.labeledFaceDescriptors && self.labeledFaceDescriptors.length != 0) {
                        await self.dialog.add(AttendanceRecognitionDialog, {
                            faceapi: faceapi,
                            labeledFaceDescriptors : self.labeledFaceDescriptors,
                            updateRecognitionAttendance: (rdata) => {
                                if (self.employee.id != rdata.employee_id){
                                    def_recognigtion.reject();
                                    return self.notificationService.add(
                                        _t("Failed: Please try again. The detected employee does not match the login employee."),
                                        { type: "danger" }
                                    );
                                }else{
                                    c_photo = rdata.image;
                                    def_recognigtion.resolve();
                                }
                            }
                        });
                    }
                    else {
                        def_recognigtion.reject();
                        self.notificationService.add(_t("Detection Failed: Resource not found, Please add it to your users profile."), {
                            type: 'danger',
                        });
                    }
                }else{
                    def_recognigtion.resolve();
                }

                const def_photo = new Deferred();
                if (self.show_photo){
                    await self.dialog.add(AttendanceWebcamDialog, {
                        uploadWebcamImage: (rdata) => {
                            if (rdata.image){
                                c_photo = rdata.image;
                                def_photo.resolve();
                            }else{
                                def_photo.reject();
                                self.notificationService.add(_t("Photo not loaded, Please try again."), {
                                    type: "danger",
                                });
                            }
                        }
                    });
                }else{
                    def_photo.resolve();
                }



                Promise.all([def_geolocation , def_geofence , def_ipaddress , def_recognigtion , def_photo , def_work_type, def_project, def_work ]).then(function () {
                    navigator.geolocation.getCurrentPosition(
                        async ({coords: {latitude, longitude}}) => {
                            await self.rpc("/hr_attendance/systray_check_in_out", {
                                latitude,
                                longitude
                            }).then(async function(data){
                                if (data.attendance.id && data.attendance_state == "checked_in"){
                                    await self.rpc("/web/dataset/call_kw/hr.attendance/write", {
                                        model: "hr.attendance",
                                        method: "write",
                                        args: [parseInt(data.attendance.id), {
                                            'check_in_latitude': c_latitude || latitude,
                                            'check_in_longitude': c_longitude || longitude,
                                            'check_in_geofence_ids': c_fence_ids,
                                            'check_in_photo': c_photo,
                                            'check_in_ipaddress': c_ipaddress,
                                            'check_in_work_type_id': parseInt(c_work_type),
                                            'check_in_project_id': parseInt(c_project),
                                            'check_in_work': c_work,
                                        }],
                                        kwargs: {},
                                    });
                                }
                                else if(data.attendance.id && data.attendance_state == "checked_out"){
                                    await self.rpc("/web/dataset/call_kw/hr.attendance/write", {
                                        model: "hr.attendance",
                                        method: "write",
                                        args: [parseInt(data.attendance.id), {
                                            'check_out_latitude': c_latitude || latitude,
                                            'check_out_longitude': c_longitude || longitude,
                                            'check_out_geofence_ids': c_fence_ids,
                                            'check_out_photo': c_photo,
                                            'check_out_ipaddress': c_ipaddress,
                                            'check_out_work_type_id': parseInt(c_work_type),
                                            'check_out_project_id': parseInt(c_project),
                                            'check_out_work': c_work,
                                        }],
                                        kwargs: {},
                                    });
                                }
                            });
                            await self.searchReadEmployee()
                        },
                        async err => {
                            await self.rpc("/hr_attendance/systray_check_in_out").then(async function(data){
                                if (data.attendance.id && data.attendance_state == "checked_in"){
                                    await self.rpc("/web/dataset/call_kw/hr.attendance/write", {
                                        model: "hr.attendance",
                                        method: "write",
                                        args: [parseInt(data.attendance.id), {
                                            'check_in_latitude': c_latitude,
                                            'check_in_longitude': c_longitude,
                                            'check_in_geofence_ids': c_fence_ids,
                                            'check_in_photo': c_photo,
                                            'check_in_ipaddress': c_ipaddress,
                                            'check_in_work_type_id': c_work_type,
                                            'check_in_project_id': c_project,
                                            'check_in_work': c_work,
                                        }],
                                        kwargs: {},
                                    });
                                }
                                else if(data.attendance.id && data.attendance_state == "checked_out"){
                                    await self.rpc("/web/dataset/call_kw/hr.attendance/write", {
                                        model: "hr.attendance",
                                        method: "write",
                                        args: [parseInt(data.attendance.id), {
                                            'check_out_latitude': c_latitude,
                                            'check_out_longitude': c_longitude,
                                            'check_out_geofence_ids': c_fence_ids,
                                            'check_out_photo': c_photo,
                                            'check_out_ipaddress': c_ipaddress,
                                            'check_out_work_type_id': c_work_type,
                                            'check_out_project_id': c_project,
                                            'check_out_work': c_work,
                                        }],
                                        kwargs: {},
                                    });
                                }
                            });
                            await self.searchReadEmployee()
                        }
                    )
                }).catch((err) => {
                    console.log(err)
                });
        }else {
            navigator.geolocation.getCurrentPosition(
                async ({coords: {latitude, longitude}}) => {
                    await self.rpc("/hr_attendance/systray_check_in_out", {
                        latitude,
                        longitude
                    })
                    await this.searchReadEmployee()
                },
                async err => {
                    await self.rpc("/hr_attendance/systray_check_in_out")
                    await self.searchReadEmployee()
                }
            )
        }
        this.reload_menu =0;
    },
});
export default ActivityMenu;