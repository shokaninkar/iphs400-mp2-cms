1. Saving a post as a draft did not put it on the public blog. The draft preview showed the title and body, but the blog itself still listed only “Hello world!”. A preview is therefore different from the public post list.

2. After publishing “3 Things to Check Before Applying to College” and reloading the public blog, the post appeared above “Hello world!” with its body and date. The editor also showed its status as Published.

3. I created and published an About page. After refreshing the site, About appeared automatically in the header navigation alongside the existing pages. The admissions post appeared in the blog list, but not in that navigation. I did not have to configure the menu for About to appear in this Playground theme.

4. Settings → Permalinks had “Day and name” selected. The published post path was `/2026/10/16/3-things-to-check-before-applying-to-college/`. WordPress used the date and turned the title into a lowercase slug with hyphens between the words. The post editor also had a Slug control in the Post settings panel.

5. The Editor account was called practice_editor. Once logged in as that account, the sidebar showed Profile instead of Users. Opening `/wp-admin/users.php` directly displayed “You need a higher level of permission.” and “Sorry, you are not allowed to list users.” Hiding a menu was not the only restriction: the server also refused the direct URL. That is relevant to inkadmissions, where an editor must not manage accounts. My custom CMS goes further by also reserving Pages and publishing for the administrator.

6. In Posts → All Posts, the status filters were above the table, under “Filter posts list”. They showed “All (2) | Published (2)”. There was no Drafts link after the only draft had been published. In my own CMS, I would keep a Drafts filter visible with a zero count so the available states are easier to discover.
