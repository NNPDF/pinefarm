c     cut for mmllmax (SFOS lepton pairs)
      do i=1,nexternal-1
        if (is_a_lm_reco(i) .or. is_a_lp_reco(i)) then
          do j=i+1,nexternal
            if (ipdg(i) .eq. -ipdg(j)) then
              if (invm2_04(p(0,i),p(0,j),1d0) .gt. {}**2) then
                passcuts_leptons=.false.
                return
              endif
            endif
          enddo
        endif
      enddo
