/**
 * 非模块版 VRButton，改自 three.js r128 examples/jsm/webxr/VRButton.js（MIT）。
 * 挂到 THREE.VRButton，供不走 ES module 的页面直接 <script> 引入。
 * 改动：按钮文案改成中文；不支持时不报错，只把状态回调给页面；样式由页面 CSS 接管。
 */
( function () {

	class VRButton {

		/**
		 * @param {THREE.WebGLRenderer} renderer  已设 renderer.xr.enabled = true
		 * @param {Object} [opts]
		 * @param {Function} [opts.onStatus]  (state, button) => {}，state ∈ 'ready' | 'unsupported' | 'insecure' | 'noxr' | 'session' | 'ended'
		 * @param {Array} [opts.optionalFeatures]
		 */
		static createButton( renderer, opts ) {

			opts = opts || {};
			const notify = typeof opts.onStatus === 'function' ? opts.onStatus : function () {};
			const button = document.createElement( 'button' );
			button.type = 'button';
			button.id = 'VRButton';
			button.className = 'vr-button';
			button.style.display = 'none';

			function showEnterVR() {

				let currentSession = null;

				async function onSessionStarted( session ) {

					session.addEventListener( 'end', onSessionEnded );
					await renderer.xr.setSession( session );
					button.textContent = '退出 VR';
					button.dataset.state = 'session';
					currentSession = session;
					notify( 'session', button, session );

				}

				function onSessionEnded() {

					currentSession.removeEventListener( 'end', onSessionEnded );
					button.textContent = '進入 VR';
					button.dataset.state = 'ready';
					currentSession = null;
					notify( 'ended', button );

				}

				button.style.display = '';
				button.textContent = '進入 VR';
				button.dataset.state = 'ready';
				button.onclick = function () {

					if ( currentSession === null ) {

						const sessionInit = {
							optionalFeatures: opts.optionalFeatures || [ 'local-floor', 'bounded-floor' ]
						};
						navigator.xr.requestSession( 'immersive-vr', sessionInit )
							.then( onSessionStarted )
							.catch( function ( err ) {

								console.warn( 'VRButton: requestSession 失敗', err );
								notify( 'error', button, err );

							} );

					} else {

						currentSession.end();

					}

				};
				notify( 'ready', button );

			}

			function showUnsupported( state ) {

				button.style.display = '';
				button.textContent = '此瀏覽器不支持 VR';
				button.dataset.state = state;
				button.disabled = true;
				button.onclick = null;
				notify( state, button );

			}

			if ( 'xr' in navigator ) {

				navigator.xr.isSessionSupported( 'immersive-vr' ).then( function ( supported ) {

					supported ? showEnterVR() : showUnsupported( 'unsupported' );

				} ).catch( function () {

					showUnsupported( 'unsupported' );

				} );

			} else if ( window.isSecureContext === false ) {

				showUnsupported( 'insecure' );

			} else {

				showUnsupported( 'noxr' );

			}

			return button;

		}

	}

	THREE.VRButton = VRButton;

} )();
