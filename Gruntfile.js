// Generated on 2014-11-29 using
// generator-webapp 0.5.1
'use strict';

module.exports = function(grunt) {
  grunt.loadNpmTasks('grunt-bower-concat');

  require('load-grunt-tasks')(grunt);

  // Project configuration
  grunt.initConfig({
    bower_concat: {
      all: {
        dest: 'static/js/bower.js'
      }
    }
  });
};
